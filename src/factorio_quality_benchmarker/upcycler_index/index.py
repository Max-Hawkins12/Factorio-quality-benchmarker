from collections.abc import Set as AbstractSet

import networkx as nx

from factorio_quality_benchmarker.model import Item, Material, Recipe

from .models import ProductionGraph, RecipeGraph, RecipeGraphIndex, UpcyclingGraph


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
    graph: nx.DiGraph, start_recipe: Recipe, end_recipe: Recipe
) -> RecipeGraph:
    if start_recipe.ingredient_items == end_recipe.product_items:
        return UpcyclingGraph(
            graph=graph,
            start_recipe=start_recipe,
            end_recipe=end_recipe,
        )

    return ProductionGraph(
        graph=graph,
        start_recipe=start_recipe,
        end_recipe=end_recipe,
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


# Public API
def generate_upcycler_index(
    materials: dict[str, Material],
    recipes: dict[str, Recipe],
) -> RecipeGraphIndex:
    """
    Returns an index of all upcycling and production graphs by the item they produce.
    """

    items = tuple(
        material for material in materials.values() if isinstance(material, Item)
    )

    producer_recipes = _get_producer_recipes(materials, recipes)

    upcycling_graphs: dict[Item, list[UpcyclingGraph]] = {item: [] for item in items}
    production_graphs: dict[Item, list[ProductionGraph]] = {item: [] for item in items}

    excluded_recipes_by_item: dict[Item, set[Recipe]] = {item: set() for item in items}

    for item in items:
        raw_graphs = _find_recipe_graphs(
            item, producer_recipes, excluded_producers=excluded_recipes_by_item[item]
        )

        for graph in raw_graphs:
            if isinstance(graph, ProductionGraph):
                production_graphs[item].append(graph)
            elif isinstance(graph, UpcyclingGraph):
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

    return RecipeGraphIndex(
        upcycling_graphs_by_item={
            item: tuple(graphs) for item, graphs in upcycling_graphs.items()
        },
        production_graphs_by_item={
            item: tuple(graphs) for item, graphs in production_graphs.items()
        },
    )
