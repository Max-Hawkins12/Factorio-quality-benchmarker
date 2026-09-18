from collections.abc import Callable, Iterable
from typing import TypeVar

from factorio_quality_benchmarker.game.models import Quality
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfiguration,
)

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import GraphState, OptimisationObjective

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


def get_frontier_recipe_configurations(
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


def _dominates(a: GraphState, b: GraphState) -> bool:
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


def add_state_to_frontier(
    frontier: list[GraphState],
    state: GraphState,
) -> None:
    for existing in frontier:
        if existing.available == state.available or _dominates(existing, state):
            return

    frontier[:] = [existing for existing in frontier if not _dominates(state, existing)]

    frontier.append(state)
