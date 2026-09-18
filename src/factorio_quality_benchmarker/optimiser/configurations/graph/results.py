from collections.abc import Mapping

from factorio_quality_benchmarker.game.models import Item, Quality, Recipe
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfiguration,
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.graphs import RecipeGraph, UpcyclingGraph
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import (
    GraphConfiguration,
    GraphMetrics,
    GraphResult,
    GraphState,
    OptimisationObjective,
)
from .pareto import add_state_to_frontier, get_frontier_recipe_configurations


# Helper methods
def _initial_state(recipe_configuration: RecipeConfiguration) -> GraphState:
    return GraphState(
        available=dict(recipe_configuration.metrics.input_items_per_craft),
        configurations={},
    )


def _recipes_at_legendary(
    target: Item,
    graph: RecipeGraph,
) -> tuple[Recipe, ...]:
    if isinstance(graph, UpcyclingGraph):
        return tuple(
            recipe
            for recipe in graph.ordered_recipes
            if target not in recipe.ingredient_items
        )

    return graph.ordered_recipes


def _legendary_per_input(
    state: GraphState,
    target: Item,
    graph: RecipeGraph,
    normal: Quality,
    legendary: Quality,
) -> float:

    legendary_output = state.available[target][legendary]

    if isinstance(graph, UpcyclingGraph) and graph.is_self_recycling:
        net_input = 1.0 - state.available[target][normal]
        return legendary_output / net_input

    return legendary_output


def _legendary_per_second(
    state: GraphState,
    target: Item,
    legendary: Quality,
) -> float:
    return state.available[target][legendary]


def _apply_recipe_configuration_to_state(
    state: GraphState,
    configuration: RecipeConfiguration,
    recipe: Recipe,
    quality: Quality,
    objective: OptimisationObjective,
) -> GraphState:

    item_inputs = configuration.metrics.input_items_per_craft

    input_limited_operations = (
        min(
            state.available[material][quality] / item_inputs[material][quality]
            for material in item_inputs
        )
        if item_inputs
        else 1.0
    )

    match objective:
        case OptimisationObjective.LEGENDARY_PER_INPUT:
            operation_throttle = input_limited_operations
        case OptimisationObjective.LEGENDARY_PER_SECOND:
            operation_throttle = min(
                input_limited_operations, configuration.metrics.crafts_per_second
            )

    if operation_throttle == 0:
        return state

    produces = {
        material: amounts.scale(operation_throttle)
        for material, amounts in configuration.metrics.output_per_craft.items()
    }

    consumes = {
        material: amounts.scale(operation_throttle)
        for material, amounts in configuration.metrics.input_per_craft.items()
    }

    materials = state.available.keys() | consumes.keys() | produces.keys()

    return GraphState(
        available={
            material: state.available.get(material, EMPTY_QUALITY_AMOUNTS)
            - consumes.get(material, EMPTY_QUALITY_AMOUNTS)
            + produces.get(material, EMPTY_QUALITY_AMOUNTS)
            for material in materials
            if isinstance(material, Item)
        },
        configurations=state.configurations
        | {Qualified(recipe, quality): configuration},
    )


def _get_frontier_states(
    states: list[GraphState],
    recipes: tuple[Recipe, ...],
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
    objective: OptimisationObjective,
) -> list[GraphState]:
    for recipe in recipes:
        configs = get_frontier_recipe_configurations(
            recipe_configuration_cache.get(recipe)[quality], quality, objective
        )

        if not recipe.ingredient_items:
            continue

        next_states: list[GraphState] = []
        for state in states:
            if all(amounts[quality] == 0 for amounts in state.available.values()):
                add_state_to_frontier(next_states, state)
                continue

            for configuration in configs:
                next_state = _apply_recipe_configuration_to_state(
                    state=state,
                    configuration=configuration,
                    recipe=recipe,
                    quality=quality,
                    objective=objective,
                )

                add_state_to_frontier(next_states, next_state)

        states = next_states

    return states


def _optimise_graph(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
    objective: OptimisationObjective,
) -> GraphConfiguration:

    normal = qualities["normal"]
    legendary = qualities["legendary"]

    states = [
        _apply_recipe_configuration_to_state(
            state=_initial_state(configuration),
            configuration=configuration,
            recipe=graph.start_recipe,
            quality=normal,
            objective=objective,
        )
        for configuration in get_frontier_recipe_configurations(
            configurations=recipe_configuration_cache.get(graph.start_recipe)[normal],
            quality=normal,
            objective=objective,
        )
    ]

    states = _get_frontier_states(
        states=states,
        recipes=graph.ordered_recipes[1:],
        quality=normal,
        recipe_configuration_cache=recipe_configuration_cache,
        objective=objective,
    )

    for quality in list(qualities.values())[1:]:
        recipes = (
            _recipes_at_legendary(target, graph)
            if quality == legendary
            else graph.ordered_recipes
        )

        states = _get_frontier_states(
            states=states,
            recipes=recipes,
            quality=quality,
            recipe_configuration_cache=recipe_configuration_cache,
            objective=objective,
        )

    match objective:
        case OptimisationObjective.LEGENDARY_PER_INPUT:
            best_state = max(
                states,
                key=lambda state: _legendary_per_input(
                    state, target, graph, normal, legendary
                ),
            )
        case OptimisationObjective.LEGENDARY_PER_SECOND:
            best_state = max(
                states,
                key=lambda state: _legendary_per_second(state, target, legendary),
            )

    return GraphConfiguration(
        recipe_configurations=best_state.configurations,
        metrics=GraphMetrics(
            legendary_per_input=_legendary_per_input(
                best_state, target, graph, normal, legendary
            ),
            legendary_per_second=_legendary_per_second(best_state, target, legendary),
        ),
    )


def optimise_graph(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
):
    return GraphResult(
        graph=graph,
        best_per_input=_optimise_graph(
            target,
            graph,
            qualities,
            recipe_configuration_cache,
            objective=OptimisationObjective.LEGENDARY_PER_INPUT,
        ),
        best_per_second=_optimise_graph(
            target,
            graph,
            qualities,
            recipe_configuration_cache,
            objective=OptimisationObjective.LEGENDARY_PER_SECOND,
        ),
    )


"""    for material, amounts in best_state.available.items():
        print(
            f"\t\t{material.name}: available: {[(quality.name, amount) for quality, amount in amounts.amounts.items()]}"
        )

    for recipe, config in best_state.configurations.items():
        print(
            f"\t{recipe.name}: modules: {[module.name for module in config.machine_configuration.modules.modules]} beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
        )
        for material, amounts in config.metrics.input_per_craft.items():
            print(
                f"\t\t{material.name}: input: {[(quality.name, amount) for quality, amount in amounts.amounts.items()]}"
            )
        for material, amounts in config.metrics.output_per_craft.items():
            print(
                f"\t\t{material.name}: output: {[(quality.name, amount) for quality, amount in amounts.amounts.items()]}"
            )

    print()"""
