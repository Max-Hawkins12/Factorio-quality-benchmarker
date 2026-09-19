from collections.abc import Mapping

from factorio_quality_benchmarker.game.models import Item, Quality, Recipe
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfiguration,
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import (
    GraphConfiguration,
    GraphMetrics,
    GraphResult,
    GraphState,
    RecipeGraph,
    UpcyclingGraph,
)
from .pareto import (
    add_state_to_frontier,
    get_frontier_recipe_configurations_throughput_ignored,
    get_frontier_recipe_configurations_throughput_observed,
)


# Helpers
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


def _advance_state(
    state: GraphState,
    configuration: RecipeConfiguration,
    throughput: float,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:
    if throughput == 0:
        return state

    produces = {
        material: amounts.scale(throughput)
        for material, amounts in configuration.metrics.output_per_craft.items()
    }

    consumes = {
        material: amounts.scale(throughput)
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


# Legendary/input optimisers
def _initial_state_throughput_ignored(
    recipe_configuration: RecipeConfiguration,
) -> GraphState:
    return GraphState(
        available=dict(recipe_configuration.metrics.input_items_per_craft),
        configurations={},
    )


def _advance_state_throughput_ignored(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:

    item_inputs = configuration.metrics.input_items_per_craft

    throughput = (
        min(
            state.available[material][quality] / item_inputs[material][quality]
            for material in item_inputs
        )
        if item_inputs
        else 1.0
    )

    return _advance_state(state, configuration, throughput, quality, recipe)


def _get_frontier_states_throughput_ignored(
    states: list[GraphState],
    recipes: tuple[Recipe, ...],
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
) -> list[GraphState]:
    for recipe in recipes:
        if not recipe.ingredient_items:
            continue

        configurations = get_frontier_recipe_configurations_throughput_ignored(
            recipe_configuration_cache.get(recipe)[quality],
            quality,
        )

        next_states: list[GraphState] = []
        for state in states:
            if all(amounts[quality] == 0 for amounts in state.available.values()):
                add_state_to_frontier(next_states, state, quality)
                continue

            for configuration in configurations:
                next_state = _advance_state_throughput_ignored(
                    state=state,
                    configuration=configuration,
                    recipe=recipe,
                    quality=quality,
                )

                add_state_to_frontier(next_states, next_state, quality)

        states = next_states

    return states


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


def _optimise_graph_per_input(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
) -> dict[Qualified[Recipe], RecipeConfiguration]:
    normal = qualities["normal"]
    legendary = qualities["legendary"]

    states = [
        _advance_state_throughput_ignored(
            state=_initial_state_throughput_ignored(configuration),
            configuration=configuration,
            recipe=graph.start_recipe,
            quality=normal,
        )
        for configuration in get_frontier_recipe_configurations_throughput_ignored(
            configurations=recipe_configuration_cache.get(graph.start_recipe)[normal],
            quality=normal,
        )
    ]

    states = _get_frontier_states_throughput_ignored(
        states=states,
        recipes=graph.ordered_recipes[1:],
        quality=normal,
        recipe_configuration_cache=recipe_configuration_cache,
    )

    for quality in list(qualities.values())[1:]:
        recipes = (
            _recipes_at_legendary(target, graph)
            if quality == legendary
            else graph.ordered_recipes
        )

        states = _get_frontier_states_throughput_ignored(
            states=states,
            recipes=recipes,
            quality=quality,
            recipe_configuration_cache=recipe_configuration_cache,
        )

    return max(
        states,
        key=lambda state: _legendary_per_input(state, target, graph, normal, legendary),
    ).configurations


# Legendary/second Methods
def _initial_state_throughput_observed(
    configuration: RecipeConfiguration,
) -> GraphState:
    throughput = configuration.metrics.crafts_per_second

    return GraphState(
        available={
            material: amounts.scale(throughput)
            for material, amounts in configuration.metrics.input_items_per_craft.items()
        },
        configurations={},
    )


def _get_throughput(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
) -> float:
    item_inputs = configuration.metrics.input_items_per_craft

    return min(
        (
            min(
                state.available[material][quality] / item_inputs[material][quality]
                for material in item_inputs
            )
            if item_inputs
            else 1.0
        ),
        configuration.metrics.crafts_per_second,
    )


def _advance_state_throughput_observed(
    state: GraphState,
    configuration: RecipeConfiguration,
    quality: Quality,
    recipe: Recipe,
) -> GraphState:

    return _advance_state(
        state,
        configuration,
        _get_throughput(state, configuration, quality),
        quality,
        recipe,
    )


def _get_frontier_states_throughput_observed(
    states: list[GraphState],
    recipes: tuple[Recipe, ...],
    quality: Quality,
    recipe_configuration_cache: RecipeConfigurationCache,
) -> list[GraphState]:
    for recipe in recipes:
        if not recipe.ingredient_items:
            continue

        next_states: list[GraphState] = []
        for state in states:
            if all(amounts[quality] == 0 for amounts in state.available.values()):
                add_state_to_frontier(next_states, state, quality)
                continue

            configurations = recipe_configuration_cache.get(recipe)[quality]

            frontier_configurations = (
                get_frontier_recipe_configurations_throughput_observed(
                    recipe_configuration_cache.get(recipe)[quality],
                    quality,
                    _get_throughput(state, configurations[0], quality),
                )
            )

            for configuration in frontier_configurations:
                next_state = _advance_state_throughput_observed(
                    state=state,
                    configuration=configuration,
                    recipe=recipe,
                    quality=quality,
                )

                add_state_to_frontier(next_states, next_state, quality)

        states = next_states

    return states


def _legendary_per_second(
    state: GraphState,
    target: Item,
    legendary: Quality,
) -> float:
    return state.available[target][legendary]


def _optimise_graph_per_second(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
) -> dict[Qualified[Recipe], RecipeConfiguration]:
    normal = qualities["normal"]
    legendary = qualities["legendary"]

    states = [
        _advance_state_throughput_observed(
            state=_initial_state_throughput_observed(configuration),
            configuration=configuration,
            recipe=graph.start_recipe,
            quality=normal,
        )
        for configuration in get_frontier_recipe_configurations_throughput_observed(
            configurations=recipe_configuration_cache.get(graph.start_recipe)[normal],
            quality=normal,
            limited_crafts_per_second=100000,
        )
    ]

    states = _get_frontier_states_throughput_observed(
        states=states,
        recipes=graph.ordered_recipes[1:],
        quality=normal,
        recipe_configuration_cache=recipe_configuration_cache,
    )

    for quality in list(qualities.values())[1:]:
        recipes = (
            _recipes_at_legendary(target, graph)
            if quality == legendary
            else graph.ordered_recipes
        )

        states = _get_frontier_states_throughput_observed(
            states=states,
            recipes=recipes,
            quality=quality,
            recipe_configuration_cache=recipe_configuration_cache,
        )

    return max(
        states,
        key=lambda state: _legendary_per_second(state, target, legendary),
    ).configurations


def _evaluate_per_input(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configs: dict[Qualified[Recipe], RecipeConfiguration],
):
    normal = qualities["normal"]
    legendary = qualities["legendary"]

    start_config = configs[Qualified(graph.start_recipe, normal)]

    state = _initial_state_throughput_ignored(start_config)

    for quality in qualities.values():
        recipes = (
            _recipes_at_legendary(target, graph)
            if quality == legendary
            else graph.ordered_recipes
        )

        for recipe in recipes:
            config = configs.get(Qualified(recipe, quality))

            if config is None:
                continue

            state = _advance_state_throughput_ignored(
                state,
                config,
                quality,
                recipe,
            )

    return _legendary_per_second(
        state,
        target,
        legendary,
    )


def _evaluate_per_second(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    configs: dict[Qualified[Recipe], RecipeConfiguration],
):
    normal = qualities["normal"]
    legendary = qualities["legendary"]

    start_config = configs[Qualified(graph.start_recipe, normal)]

    state = _initial_state_throughput_observed(start_config)

    for quality in qualities.values():
        recipes = (
            _recipes_at_legendary(target, graph)
            if quality == legendary
            else graph.ordered_recipes
        )

        for recipe in recipes:
            config = configs.get(Qualified(recipe, quality))

            if config is None:
                continue

            state = _advance_state_throughput_observed(
                state,
                config,
                quality,
                recipe,
            )

    return _legendary_per_second(
        state,
        target,
        legendary,
    )


def generate_graph_results(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
) -> GraphResult:

    best_per_input = _optimise_graph_per_input(
        target, graph, qualities, recipe_configuration_cache
    )
    best_per_second = _optimise_graph_per_second(
        target, graph, qualities, recipe_configuration_cache
    )

    print(
        f"Best /input: legendary/input: {_evaluate_per_input(target, graph, qualities, best_per_input)} legendary/second: {_evaluate_per_second(target, graph, qualities, best_per_input)}"
    )
    for recipe, config in best_per_input.items():
        print(
            f"\t{recipe.name}: modules: {[module.name for module in config.machine_configuration.modules.modules]} beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
        )
    print(
        f"Best /second: legendary/input: {_evaluate_per_input(target, graph, qualities, best_per_second)} legendary/second: {_evaluate_per_second(target, graph, qualities, best_per_second)}"
    )
    for recipe, config in best_per_second.items():
        print(
            f"\t{recipe.name}: modules: {[module.name for module in config.machine_configuration.modules.modules]} beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
        )

    return GraphResult(
        graph=graph,
        best_per_input=GraphConfiguration(
            recipe_configurations=best_per_input,
            metrics=GraphMetrics(
                legendary_per_input=_evaluate_per_input(
                    target, graph, qualities, best_per_input
                ),
                legendary_per_second=_evaluate_per_second(
                    target, graph, qualities, best_per_input
                ),
            ),
        ),
        best_per_second=GraphConfiguration(
            recipe_configurations=best_per_second,
            metrics=GraphMetrics(
                legendary_per_input=_evaluate_per_input(
                    target, graph, qualities, best_per_second
                ),
                legendary_per_second=_evaluate_per_second(
                    target, graph, qualities, best_per_second
                ),
            ),
        ),
    )
