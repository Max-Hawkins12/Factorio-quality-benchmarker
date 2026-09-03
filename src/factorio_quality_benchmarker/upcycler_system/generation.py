from collections.abc import Iterable
from collections.abc import Set as AbstractSet
from itertools import product as CartesianProduct

import networkx as nx

from factorio_quality_benchmarker.model import (
    FluidIngredient,
    Item,
    ItemIngredient,
    ItemProduct,
    Material,
    Recipe,
    Resource,
)

from .models import (
    RecipeIndex,
    UpcyclerGraph,
    UpcyclerSystem,
)


# Recipe Helpers
def _get_recipe_input_items(recipe: Recipe) -> tuple[Item, ...]:
    return tuple(
        ingredient.item
        for ingredient in recipe.ingredients
        if isinstance(ingredient, ItemIngredient)
    )


def _get_recipe_output_items(recipe: Recipe) -> tuple[Item, ...]:
    return tuple(
        product.item for product in recipe.products if isinstance(product, ItemProduct)
    )


def _unique_materials(materials: Iterable[Material]) -> tuple[Material, ...]:
    """Return materials in first-seen order with duplicates removed."""
    return tuple(dict.fromkeys(materials))


def _get_graph_input_fluids(graph: nx.DiGraph) -> tuple[Material, ...]:
    """
    Return every quality-less material input used by recipes in the graph.

    Item inputs are deliberately excluded. The item part of the graph boundary is
    supplied separately by the search, while fluids remain external inputs wherever
    they occur in the chain.
    """
    return _unique_materials(
        ingredient.material
        for node in graph.nodes
        if isinstance(node, Recipe)
        for ingredient in node.ingredients
        if isinstance(ingredient, FluidIngredient)
    )


def _make_input_materials(
    graph: nx.DiGraph,
    boundary_items: Iterable[Item],
) -> tuple[Material, ...]:
    """
    Build the simulation boundary for an upcycler graph.

    Boundary items say where the quality-bearing chain begins. Fluids are added from
    every recipe in the graph because they are external, quality-less inputs even if
    consumed later in the chain.
    """
    return _unique_materials((*boundary_items, *_get_graph_input_fluids(graph)))


# Graph Helpers
def _add_recycling_loop(
    graph: nx.DiGraph,
    target: Item,
    recycling_recipe: Recipe,
    recycling_products: tuple[Item, ...],
) -> None:
    graph.add_edge(target, recycling_recipe)
    graph.add_edges_from((recycling_recipe, product) for product in recycling_products)


def _is_recipe_ingredient_raw_resource(
    item: Item,
    raw_resources: AbstractSet[Resource],
) -> bool:
    return any(
        item == resource.product.item
        for resource in raw_resources
        if isinstance(resource.product, ItemProduct)
    )


def _is_valid_upcycler_graph(graph: nx.DiGraph) -> bool:
    return all(graph.out_degree(node) > 0 for node in graph.nodes)


def _get_start_recipe(
    graph: nx.DiGraph,
    input_items: tuple[Item, ...],
) -> Recipe:
    start_recipes = {
        successor
        for item in input_items
        for successor in graph.successors(item)
        if isinstance(successor, Recipe)
    }

    if len(start_recipes) != 1:
        raise ValueError(
            f"Expected exactly one start recipe, found "
            f"{len(start_recipes)}: "
            f"{[recipe.name for recipe in start_recipes]}"
        )

    return next(iter(start_recipes))


# Upcycler Core Discovery
def _find_core_crafting_graphs(
    item: Item,
    available_items: set[Item],
    recipe_index: RecipeIndex,
    visiting: set[Item] | None = None,
    forbidden_items: AbstractSet[Item] = frozenset(),
) -> tuple[nx.DiGraph, ...]:

    if item in available_items:
        graph = nx.DiGraph()
        graph.add_node(item)
        return (graph,)

    if item in forbidden_items:
        return ()

    if visiting is None:
        visiting = set()

    if item in visiting:
        return ()

    visiting = visiting | {item}
    solutions: list[nx.DiGraph] = []

    for recipe in recipe_index.crafter_producers_by_material[item]:
        ingredient_solutions: list[tuple[Item, tuple[nx.DiGraph, ...]]] = []
        valid = True

        for ingredient in recipe.ingredients:
            if not isinstance(ingredient, ItemIngredient):
                continue

            ingredient_item = ingredient.item

            if ingredient_item in forbidden_items:
                valid = False
                break

            ingredient_graphs = _find_core_crafting_graphs(
                ingredient_item,
                available_items,
                recipe_index,
                visiting,
                forbidden_items,
            )

            if not ingredient_graphs:
                valid = False
                break

            ingredient_solutions.append((ingredient_item, ingredient_graphs))

        if not valid:
            continue

        for graph_combination in CartesianProduct(
            *(graphs for _, graphs in ingredient_solutions)
        ):
            graph = nx.DiGraph()
            graph.add_edge(recipe, item)

            for (ingredient_item, _), ingredient_graph in zip(
                ingredient_solutions,
                graph_combination,
            ):
                graph = nx.compose(
                    graph,
                    ingredient_graph,
                )
                graph.add_edge(ingredient_item, recipe)

            solutions.append(graph)

    return tuple(solutions)


def _find_loop_core_from_target_as_recycler_output(
    target: Item,
    recipe_index: RecipeIndex,
) -> tuple[UpcyclerGraph, ...]:
    recycling_recipes = recipe_index.recycler_producers_by_material[target]
    valid_graphs: list[UpcyclerGraph] = []

    for recipe in recycling_recipes:
        recycling_products = _get_recipe_output_items(recipe)
        recycling_inputs = _get_recipe_input_items(recipe)

        if len(recycling_inputs) != 1:
            raise ValueError(
                f"{recipe.name} should only have one input item, "
                f"but it has {len(recycling_inputs)}"
            )

        recycling_input = recycling_inputs[0]
        crafting_graphs = _find_core_crafting_graphs(
            recycling_input,
            set(recycling_products),
            recipe_index,
        )

        for graph in crafting_graphs:
            start_recipe = (
                _get_start_recipe(graph, recycling_products)
                if recycling_input != (target)
                else recipe
            )

            _add_recycling_loop(
                graph,
                recycling_input,
                recipe,
                recycling_products,
            )

            if _is_valid_upcycler_graph(graph):
                valid_graphs.append(
                    UpcyclerGraph(
                        graph=graph,
                        start_recipe=start_recipe,
                        input_materials=_make_input_materials(
                            graph,
                            recycling_products,
                        ),
                    )
                )

    return tuple(valid_graphs)


def _find_loop_core_from_target_as_recycler_input(
    target: Item,
    recipe_index: RecipeIndex,
) -> tuple[UpcyclerGraph, ...]:
    recycling_recipe = recipe_index.recycler_consumers_by_material[target]
    recycling_products = _get_recipe_output_items(recycling_recipe)

    crafting_graphs = _find_core_crafting_graphs(
        target,
        set(recycling_products),
        recipe_index,
    )

    valid_graphs: list[UpcyclerGraph] = []

    for graph in crafting_graphs:
        start_recipe = _get_start_recipe(graph, recycling_products)

        _add_recycling_loop(
            graph,
            target,
            recycling_recipe,
            recycling_products,
        )

        if _is_valid_upcycler_graph(graph):
            valid_graphs.append(
                UpcyclerGraph(
                    graph=graph,
                    start_recipe=start_recipe,
                    input_materials=_make_input_materials(
                        graph,
                        recycling_products,
                    ),
                )
            )

    return tuple(valid_graphs)


def _find_loop_cores(
    target: Item,
    recipe_index: RecipeIndex,
) -> tuple[UpcyclerGraph, ...]:
    """Find the mandatory recycling loop(s) for a target."""
    target_recycling_recipe = recipe_index.recycler_consumers_by_material[target]
    output_recycling_recipes = recipe_index.recycler_producers_by_material[target]

    output_cores = _find_loop_core_from_target_as_recycler_output(
        target,
        recipe_index,
    )

    input_cores: tuple[UpcyclerGraph, ...] = ()

    if target_recycling_recipe not in output_recycling_recipes:
        input_cores = _find_loop_core_from_target_as_recycler_input(
            target,
            recipe_index,
        )

    return output_cores + input_cores


# Upcycler Subsystem Discovery
def _find_simple_loop_subgraphs(
    item: Item,
    recipe_index: RecipeIndex,
    raw_resources: AbstractSet[Resource],
    visiting: set[Item] | None = None,
    forbidden_items: AbstractSet[Item] = frozenset(),
) -> tuple[UpcyclerGraph, ...]:
    """
    Search backwards for extensions to an upcycler graph.

    A recipe with multiple item inputs forms the external quality-bearing
    boundary of the graph, so backwards expansion stops at that recipe.
    """
    if visiting is None:
        visiting = set()

    if item in visiting or item in forbidden_items:
        return ()

    visiting = visiting | {item}
    solutions: list[UpcyclerGraph] = []

    for recipe in recipe_index.crafter_producers_by_material[item]:
        input_items = _get_recipe_input_items(recipe)

        if any(input_item in forbidden_items for input_item in input_items):
            continue

        graph = nx.DiGraph()
        graph.add_edge(recipe, item)
        graph.add_edges_from((input_item, recipe) for input_item in input_items)

        # No quality-bearing item dependency: fluids (if any) are the boundary.
        if len(input_items) == 0:
            solutions.append(
                UpcyclerGraph(
                    graph=graph,
                    start_recipe=recipe,
                    input_materials=_make_input_materials(graph, ()),
                )
            )
            continue

        # Multiple quality-bearing inputs form the graph boundary.
        if len(input_items) > 1:
            solutions.append(
                UpcyclerGraph(
                    graph=graph,
                    start_recipe=recipe,
                    input_materials=_make_input_materials(graph, input_items),
                )
            )
            continue

        input_item = input_items[0]

        if _is_recipe_ingredient_raw_resource(input_item, raw_resources):
            solutions.append(
                UpcyclerGraph(
                    graph=graph,
                    start_recipe=recipe,
                    input_materials=_make_input_materials(graph, (input_item,)),
                )
            )

        subgraphs = _find_simple_loop_subgraphs(
            input_item,
            recipe_index,
            raw_resources,
            visiting,
            forbidden_items=forbidden_items,
        )

        for subgraph in subgraphs:
            combined_graph = nx.compose(graph, subgraph.graph)
            solutions.append(
                UpcyclerGraph(
                    graph=combined_graph,
                    start_recipe=recipe,
                    input_materials=_make_input_materials(
                        combined_graph,
                        subgraph.input_items,
                    ),
                )
            )

    # A recycler that produces this item can also be an upstream step.
    for recycling_recipe in recipe_index.recycler_producers_by_material[item]:
        recycling_inputs = _get_recipe_input_items(recycling_recipe)

        if len(recycling_inputs) != 1:
            raise ValueError(
                f"{recycling_recipe.name} should only require one ingredient, "
                f"but it requires {len(recycling_inputs)}."
            )

        recycled_item = recycling_inputs[0]

        crafting_subgraphs = _find_simple_loop_subgraphs(
            recycled_item,
            recipe_index,
            raw_resources,
            visiting,
            forbidden_items=forbidden_items | {item},
        )

        for crafting_subgraph in crafting_subgraphs:
            graph = nx.DiGraph()
            graph.add_edge(recycled_item, recycling_recipe)

            for product in _get_recipe_output_items(recycling_recipe):
                graph.add_edge(recycling_recipe, product)

            graph = nx.compose(graph, crafting_subgraph.graph)

            solutions.append(
                UpcyclerGraph(
                    graph=graph,
                    start_recipe=recycling_recipe,
                    input_materials=_make_input_materials(
                        graph,
                        crafting_subgraph.input_items,
                    ),
                )
            )

    return tuple(solutions)


# Deduplication
def _upcycler_graph_key(
    upcycler: UpcyclerGraph,
) -> tuple[frozenset, frozenset, frozenset[Material]]:
    return (
        frozenset(upcycler.graph.nodes),
        frozenset(upcycler.graph.edges),
        frozenset(upcycler.input_materials),
    )


def _deduplicate_upcyclers(
    upcyclers: Iterable[UpcyclerGraph],
) -> tuple[UpcyclerGraph, ...]:
    unique: dict[tuple, UpcyclerGraph] = {}

    for upcycler in upcyclers:
        unique.setdefault(_upcycler_graph_key(upcycler), upcycler)

    return tuple(unique.values())


# Public API
def find_crafting_loops(
    target: Item,
    recipe_index: RecipeIndex,
    raw_resources: AbstractSet[Resource],
) -> UpcyclerSystem:
    """
    Find ordinary upcyclers only.

    This phase never attempts to collapse a multi-item input boundary by crafting
    some of those inputs from another boundary input.
    """
    cores = _find_loop_cores(target, recipe_index)
    crafting_loops: list[UpcyclerGraph] = list(cores)

    for core in cores:
        # A multi-input core is already a valid simple upcycler. The simple search
        # deliberately stops at that boundary.
        if len(core.input_items) != 1:
            continue

        subgraphs = _find_simple_loop_subgraphs(
            core.input_items[0],
            recipe_index,
            raw_resources,
        )

        for subgraph in subgraphs:
            graph = nx.compose(core.graph, subgraph.graph)

            if _is_valid_upcycler_graph(graph):
                crafting_loops.append(
                    UpcyclerGraph(
                        graph=graph,
                        start_recipe=subgraph.start_recipe,
                        input_materials=_make_input_materials(
                            graph,
                            subgraph.input_items,
                        ),
                    )
                )

    return UpcyclerSystem(
        target=target,
        upcyclers=_deduplicate_upcyclers(crafting_loops),
    )


def generate_upcycler_systems(
    items: tuple[Item, ...],
    recipe_index: RecipeIndex,
    raw_resources: AbstractSet[Resource],
) -> tuple[UpcyclerSystem, ...]:
    return tuple(
        find_crafting_loops(
            item,
            recipe_index,
            raw_resources,
        )
        for item in items
    )
