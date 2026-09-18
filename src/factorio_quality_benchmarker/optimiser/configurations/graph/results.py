from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum, auto

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Item, Quality, Recipe
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfiguration,
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.graphs import (
    RecipeGraph,
    UpcyclingGraph,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .models import GraphConfiguration, GraphMetrics, GraphResult


class OptimisationObjective(Enum):
    LEGENDARY_PER_INPUT = auto()
    LEGENDARY_PER_SECOND = auto()


EMPTY_QUALITY_AMOUNTS = QualityAmounts({})


@dataclass(slots=True)
class _GraphState:
    available: dict[Item, QualityAmounts]
    configurations: dict[Qualified[Recipe], RecipeConfiguration]


def _initial_state(recipe_configuration: RecipeConfiguration) -> _GraphState:
    return _GraphState(
        available=dict(recipe_configuration.metrics.input_items_per_craft),
        configurations={},
    )


def _apply_configuration(
    state: _GraphState,
    recipe: Recipe,
    configuration: RecipeConfiguration,
    quality: Quality,
    objective: OptimisationObjective,
) -> _GraphState:

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

    return _GraphState(
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


def _dominates(a: _GraphState, b: _GraphState) -> bool:
    materials = a.available.keys() | b.available.keys()

    greater = False

    for material in materials:
        a_amounts = a.available.get(material, EMPTY_QUALITY_AMOUNTS)
        b_amounts = b.available.get(material, EMPTY_QUALITY_AMOUNTS)

        qualities = a_amounts.amounts.keys() | b_amounts.amounts.keys()

        for quality in qualities:
            if a_amounts[quality] < b_amounts[quality]:
                return False

            if a_amounts[quality] > b_amounts[quality]:
                greater = True

    return greater


def _add_to_frontier(
    frontier: list[_GraphState],
    state: _GraphState,
) -> None:
    for existing in frontier:
        if existing.available == state.available or _dominates(existing, state):
            return

    frontier[:] = [existing for existing in frontier if not _dominates(state, existing)]

    frontier.append(state)


from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def _pareto_frontier[T](
    values: Iterable[T],
    key: Callable[[T], tuple[float, ...]],
) -> tuple[T, ...]:
    frontier: list[tuple[T, tuple[float, ...]]] = []

    for value in values:
        metrics = key(value)

        if any(
            all(a >= b for a, b in zip(existing_metrics, metrics))
            for _, existing_metrics in frontier
        ):
            continue

        frontier = [
            (existing, existing_metrics)
            for existing, existing_metrics in frontier
            if not all(a >= b for a, b in zip(metrics, existing_metrics))
        ]

        frontier.append((value, metrics))

    return tuple(value for value, _ in frontier)


def _get_relevant_graph_configurations(
    configurations: tuple[RecipeConfiguration, ...],
    quality: Quality,
    objective: OptimisationObjective,
) -> tuple[RecipeConfiguration, ...]:
    materials = tuple(configurations[0].metrics.total_per_craft.keys())

    match objective:
        case OptimisationObjective.LEGENDARY_PER_INPUT:
            return _pareto_frontier(
                configurations,
                key=lambda config: tuple(
                    value
                    for material in materials
                    for value in (
                        config.metrics.total_per_craft[material],
                        config.metrics.total_per_craft_above(quality)[material],
                    )
                ),
            )
        case OptimisationObjective.LEGENDARY_PER_SECOND:
            return _pareto_frontier(
                configurations,
                key=lambda config: tuple(
                    value
                    for material in materials
                    for value in (
                        config.metrics.total_per_craft[material],
                        config.metrics.total_per_craft_above(quality)[material],
                        config.metrics.total_per_second[material],
                        config.metrics.total_per_second_above(quality)[material],
                    )
                ),
            )


def _legendary_recipes(
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
    state: _GraphState,
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
    state: _GraphState,
    target: Item,
    legendary: Quality,
) -> float:
    return state.available[target][legendary]


def _optimise_graph(
    target: Item,
    graph: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
    objective: OptimisationObjective,
) -> GraphConfiguration:
    states = [
        _apply_configuration(
            _initial_state(configuration),
            graph.start_recipe,
            configuration,
            qualities["normal"],
            objective,
        )
        for configuration in _get_relevant_graph_configurations(
            recipe_configuration_cache.get(graph.start_recipe)[qualities["normal"]],
            qualities["normal"],
            objective,
        )
    ]

    for recipe in graph.ordered_recipes[1:]:
        configs = _get_relevant_graph_configurations(
            recipe_configuration_cache.get(recipe)[qualities["normal"]],
            qualities["normal"],
            objective,
        )

        next_states: list[_GraphState] = []
        for state in states:
            for configuration in configs:
                next_state = _apply_configuration(
                    state, recipe, configuration, qualities["normal"], objective
                )

                _add_to_frontier(next_states, next_state)

        states = next_states

    for quality in list(qualities.values())[1:]:
        recipes = (
            _legendary_recipes(target, graph)
            if quality == qualities["legendary"]
            else graph.ordered_recipes
        )

        for recipe in recipes:
            configs = _get_relevant_graph_configurations(
                recipe_configuration_cache.get(recipe)[quality], quality, objective
            )

            if not recipe.ingredient_items:
                continue

            next_states: list[_GraphState] = []
            for state in states:
                if all(amounts[quality] == 0 for amounts in state.available.values()):
                    _add_to_frontier(next_states, state)
                    continue

                for configuration in configs:
                    next_state = _apply_configuration(
                        state, recipe, configuration, quality, objective
                    )

                    _add_to_frontier(next_states, next_state)

            states = next_states

    match objective:
        case OptimisationObjective.LEGENDARY_PER_INPUT:
            best_state = max(
                states,
                key=lambda state: _legendary_per_input(
                    state, target, graph, qualities["normal"], qualities["legendary"]
                ),
            )
        case OptimisationObjective.LEGENDARY_PER_SECOND:
            best_state = max(
                states,
                key=lambda state: _legendary_per_second(
                    state, target, qualities["legendary"]
                ),
            )

    for material, amounts in best_state.available.items():
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

    return GraphConfiguration(
        recipe_configurations=best_state.configurations,
        metrics=GraphMetrics(
            legendary_per_input=_legendary_per_input(
                best_state,
                target,
                graph,
                qualities["normal"],
                qualities["legendary"],
            ),
            legendary_per_second=_legendary_per_second(
                best_state, target, qualities["legendary"]
            ),
        ),
    )


def optimise_upcycler(
    target: Item,
    upcycler: RecipeGraph,
    qualities: Mapping[str, Quality],
    recipe_configuration_cache: RecipeConfigurationCache,
):
    return GraphResult(
        graph=upcycler,
        best_per_input=_optimise_graph(
            target,
            upcycler,
            qualities,
            recipe_configuration_cache,
            objective=OptimisationObjective.LEGENDARY_PER_INPUT,
        ),
        best_per_second=_optimise_graph(
            target,
            upcycler,
            qualities,
            recipe_configuration_cache,
            objective=OptimisationObjective.LEGENDARY_PER_SECOND,
        ),
    )
