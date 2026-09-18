from collections.abc import Callable, Iterable
from typing import TypeVar

from factorio_quality_benchmarker.game.models import Quality
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfiguration,
)

from .constants import EMPTY_QUALITY_AMOUNTS
from .models import GraphState

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


def get_frontier_recipe_configurations_throughput_ignored(
    configurations: tuple[RecipeConfiguration, ...],
    quality: Quality,
):
    return _pareto_frontier(
        configurations,
        key=lambda config: tuple(
            value
            for material in tuple(configurations[0].metrics.total_per_craft.keys())
            for value in (
                config.metrics.total_per_craft[material],
                config.metrics.total_per_craft_above(quality)[material],
            )
        ),
    )


def get_frontier_recipe_configurations_throughput_observed(
    configurations: tuple[RecipeConfiguration, ...],
    quality: Quality,
    limited_crafts_per_second: float | None = None,
):
    def throughput(configuration: RecipeConfiguration) -> float:
        if limited_crafts_per_second is None:
            return configuration.metrics.crafts_per_second

        return min(
            limited_crafts_per_second,
            configuration.metrics.crafts_per_second,
        )

    return _pareto_frontier(
        configurations,
        key=lambda config: tuple(
            value
            for material in tuple(configurations[0].metrics.total_per_craft.keys())
            for value in (
                config.metrics.total_per_craft[material] * throughput(config),
                config.metrics.total_per_craft_above(quality)[material]
                * throughput(config),
            )
        ),
    )


def _dominates(a: GraphState, b: GraphState, minimum_quality: Quality) -> bool:
    materials = a.available.keys() | b.available.keys()

    greater = False

    for material in materials:
        a_amounts = a.available.get(material, EMPTY_QUALITY_AMOUNTS)
        b_amounts = b.available.get(material, EMPTY_QUALITY_AMOUNTS)

        qualities = {
            quality
            for quality in a_amounts.amounts.keys() | b_amounts.amounts.keys()
            if quality.level >= minimum_quality.level
        }

        for quality in qualities:
            if a_amounts[quality] < b_amounts[quality]:
                return False

            if a_amounts[quality] > b_amounts[quality]:
                greater = True

    return greater


def add_state_to_frontier(
    frontier: list[GraphState],
    state: GraphState,
    minimum_quality: Quality,
) -> None:
    for existing in frontier:
        if existing.available == state.available or _dominates(
            existing, state, minimum_quality
        ):
            return

    frontier[:] = [
        existing
        for existing in frontier
        if not _dominates(state, existing, minimum_quality)
    ]

    frontier.append(state)
