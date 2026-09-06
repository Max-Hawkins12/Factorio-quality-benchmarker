import logging
from collections.abc import Set as AbstractSet
from time import perf_counter

import networkx as nx

from factorio_quality_benchmarker.model import Item, Material, Recipe

from .models import ProductionGraph, RecipeGraph, RecipeGraphIndex, UpcyclingGraph

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
def _find_recipe_graphs(
    item: Item,
    producer_recipes: dict[Material, tuple[Recipe, ...]],
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

        for upstream in _find_recipe_graphs(
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


def _get_producer_recipes(
    materials: dict[str, Material],
    recipes: dict[str, Recipe],
) -> dict[Material, tuple[Recipe, ...]]:
    """
    Returns an index of every recipe by the material they produce
    """
    producer_recipes: dict[Material, list[Recipe]] = {
        material: [] for material in materials.values()
    }

    for recipe in recipes.values():
        for material in recipe.product_materials:
            producer_recipes[material].append(recipe)

    return {material: tuple(recipe) for material, recipe in producer_recipes.items()}


# Public API
def generate_upcycler_index(
    materials: dict[str, Material],
    recipes: dict[str, Recipe],
) -> RecipeGraphIndex:
    """Returns an index of all upcycling and production graphs by the item they produce."""
    start_time = perf_counter()

    items = tuple(
        material for material in materials.values() if isinstance(material, Item)
    )

    logger.info(
        "Generating recipe graph index for %d items from %d recipes",
        len(items),
        len(recipes),
    )

    producer_recipes = _get_producer_recipes(materials, recipes)

    upcycling_graphs: dict[Item, list[UpcyclingGraph]] = {item: [] for item in items}
    production_graphs: dict[Item, list[ProductionGraph]] = {item: [] for item in items}

    excluded_recipes_by_item: dict[Item, set[Recipe]] = {item: set() for item in items}

    for item in items:
        excluded_producers = excluded_recipes_by_item[item]
        excluded_producer_count = len(excluded_producers)

        raw_graphs = _find_recipe_graphs(
            item,
            producer_recipes,
            excluded_producers=excluded_producers,
        )

        production_count = 0
        upcycling_count = 0

        for graph in raw_graphs:
            if isinstance(graph, ProductionGraph):
                production_count += 1
                production_graphs[item].append(graph)

            elif isinstance(graph, UpcyclingGraph):
                upcycling_count += 1

                for output_item in graph.output_items:
                    if graph not in upcycling_graphs[output_item]:
                        upcycling_graphs[output_item].append(graph)
                        excluded_recipes_by_item[output_item].add(graph.end_recipe)

                intermediate_item = graph.intermediate_upcycled_item

                if (
                    intermediate_item
                    and graph not in upcycling_graphs[intermediate_item]
                ):
                    upcycling_graphs[intermediate_item].append(graph)

        logger.debug(
            "%s: found %d graphs (%d production, %d upcycling), %d upcyclers already covered",
            item.name,
            len(raw_graphs),
            production_count,
            upcycling_count,
            excluded_producer_count,
        )

    index = RecipeGraphIndex(
        upcycling_graphs_by_item={
            item: tuple(graphs) for item, graphs in upcycling_graphs.items()
        },
        production_graphs_by_item={
            item: tuple(graphs) for item, graphs in production_graphs.items()
        },
    )

    logger.info(
        "Generated recipe graph index in %.2fs: %d production graph references, %d upcycling graph references",
        perf_counter() - start_time,
        sum(len(graphs) for graphs in production_graphs.values()),
        sum(len(graphs) for graphs in upcycling_graphs.values()),
    )

    return index
