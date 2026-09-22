import logging
from collections import defaultdict
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field

import networkx as nx

from factorio_quality_benchmarker.game.models import Item, Material, Recipe

from .models import ProductionGraph, RecipeGraph, UpcyclerSystem, UpcyclingGraph

logger = logging.getLogger(__name__)


# Graph Helpers
def _make_graph_of_recipe(recipe: Recipe) -> nx.DiGraph:
    """
    Make a directed graph of a recipe and its ingredients and products
    """
    graph = nx.DiGraph()
    graph.add_edges_from(
        (ingredient, recipe) for ingredient in recipe.ingredient_materials
    )
    graph.add_edges_from((recipe, product) for product in recipe.product_materials)

    return graph


def _make_recipe_graph(
    graph: nx.DiGraph,
    start_recipe: Recipe,
    end_recipe: Recipe,
) -> RecipeGraph:
    if UpcyclingGraph.is_valid(graph, start_recipe, end_recipe):
        return UpcyclingGraph(
            graph=graph,
            start_recipe=start_recipe,
            end_recipe=end_recipe,
        )
    elif ProductionGraph.is_valid(graph, start_recipe, end_recipe):
        return ProductionGraph(
            graph=graph,
            start_recipe=start_recipe,
            end_recipe=end_recipe,
        )

    raise ValueError(
        f"Bad recipe graph, start recipe: {start_recipe.name}, end recipe: {end_recipe.name}"
    )


# Recursive recipe search
def _discover_recipe_graphs(
    item: Item,
    producer_recipes: Mapping[Material, tuple[Recipe, ...]],
    *,
    excluded_producers: AbstractSet[Recipe] = frozenset(),
    visiting: frozenset[Item] = frozenset(),
    forbidden_items: AbstractSet[Item] = frozenset(),
) -> tuple[RecipeGraph, ...]:
    if item in visiting or item in forbidden_items:
        return ()

    visiting = visiting | {item}
    graphs: list[RecipeGraph] = []

    for recipe in producer_recipes[item]:
        if recipe in excluded_producers:
            continue

        graph = _make_graph_of_recipe(recipe)

        if len(recipe.product_items) == 1:
            graphs.append(
                _make_recipe_graph(
                    graph=graph,
                    start_recipe=recipe,
                    end_recipe=recipe,
                )
            )

        # Only a single-item-ingredient recipe can be extended
        if len(recipe.ingredient_items) != 1:
            continue

        ingredient = recipe.ingredient_items[0]

        # Guard against infinite recursion on the same item
        if ingredient in visiting or ingredient in forbidden_items:
            continue

        upstream_forbidden_items = (
            forbidden_items | {item} if recipe.is_recycling else forbidden_items
        )

        for upstream in _discover_recipe_graphs(
            ingredient,
            producer_recipes,
            visiting=visiting,
            forbidden_items=upstream_forbidden_items,
        ):
            composed = nx.compose(graph, upstream.graph)
            start_recipe = upstream.start_recipe
            end_recipe = recipe

            if UpcyclingGraph.is_valid(
                composed,
                start_recipe,
                end_recipe,
            ) or ProductionGraph.is_valid(
                composed,
                start_recipe,
                end_recipe,
            ):
                graphs.append(
                    _make_recipe_graph(
                        graph=composed,
                        start_recipe=upstream.start_recipe,
                        end_recipe=recipe,
                    )
                )

    return tuple(graphs)


# Public cache
@dataclass(slots=True)
class UpcyclerSystemCache:
    producer_recipes: Mapping[Material, tuple[Recipe, ...]]
    recycling_recipes: Mapping[Item, Recipe]

    _graphs: dict[Item, set[RecipeGraph]] = field(
        default_factory=lambda: defaultdict(set)
    )
    _searched: set[Item] = field(default_factory=set)

    def _discover(self, item: Item) -> None:
        raw_graphs = _discover_recipe_graphs(
            item,
            self.producer_recipes,
            excluded_producers={graph.end_recipe for graph in self._graphs[item]},
        )

        for graph in raw_graphs:
            if isinstance(graph, ProductionGraph):
                self._graphs[item].add(graph)
            elif isinstance(graph, UpcyclingGraph):
                for output_item in graph.output_items:
                    self._graphs[output_item].add(graph)

                self._graphs[graph.recycled_item].add(graph)

    def _get(self, item: Item) -> tuple[RecipeGraph, ...]:
        if item not in self._searched:
            self._discover(item)

            recycling_recipe = self.recycling_recipes[item]

            if recycling_recipe.product_items != (item,):
                self._discover(recycling_recipe.product_items[0])

            self._searched.add(item)

        return tuple(
            sorted(
                self._graphs.get(item, ()),
                key=lambda graph: (
                    graph.start_recipe.name,
                    graph.end_recipe.name,
                ),
            )
        )

    def _get_upcyclers(self, item: Item) -> tuple[UpcyclingGraph, ...]:
        return tuple(
            graph for graph in self._get(item) if isinstance(graph, UpcyclingGraph)
        )

    def _get_producers(self, item: Item) -> tuple[ProductionGraph, ...]:
        return tuple(
            graph for graph in self._get(item) if isinstance(graph, ProductionGraph)
        )

    def get(self, item: Item) -> tuple[UpcyclerSystem, ...]:
        systems: list[UpcyclerSystem] = []

        for upcycler in self._get_upcyclers(item):
            systems.append(UpcyclerSystem(upcycler=upcycler))

            if len(upcycler.input_items) == 1:
                systems.extend(
                    UpcyclerSystem(
                        upcycler=upcycler,
                        before_production_graph=producer,
                    )
                    for producer in self._get_producers(upcycler.input_items[0])
                )

        for after_producer in self._get_producers(item):
            if len(after_producer.input_items) != 1:
                continue

            for upcycler in self._get_upcyclers(after_producer.input_items[0]):
                systems.append(
                    UpcyclerSystem(
                        upcycler=upcycler,
                        after_production_graph=after_producer,
                    )
                )

                if len(upcycler.input_items) == 1:
                    systems.extend(
                        UpcyclerSystem(
                            upcycler=upcycler,
                            before_production_graph=before_producer,
                            after_production_graph=after_producer,
                        )
                        for before_producer in self._get_producers(
                            upcycler.input_items[0]
                        )
                    )

        return tuple(systems)
