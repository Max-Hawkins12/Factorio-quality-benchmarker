from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.engine import (
    MAXIMUM_PRODUCTIVITY,
    MachineEffects,
    get_qualified_crafting_speed,
    productivity_bonus,
    quality_bonus,
    speed_bonus,
)
from factorio_quality_benchmarker.game.models import Crafter, Item, Recipe
from factorio_quality_benchmarker.optimiser.machines import MachineConfiguration
from factorio_quality_benchmarker.optimiser.simulation import Qualified


@dataclass(frozen=True, slots=True)
class RecipeFrontierCandidate:
    crafter: Qualified[Crafter]
    machine_configuration: MachineConfiguration

    objectives: tuple[float, float, float, float]


def calculate_recipe_objectives(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_effects: MachineEffects,
    productivity_research_index: Mapping[Item, int],
) -> tuple[float, float, float, float]:
    """This is a cheap operation for calculating an estimate of the recipe metrics"""
    productivity = 1.0 + min(
        productivity_bonus(
            recipe,
            crafter,
            machine_effects,
            productivity_research_index,
        ),
        MAXIMUM_PRODUCTIVITY,
    )

    total_per_craft = recipe.products[0].amount * productivity

    crafts_per_second = (
        get_qualified_crafting_speed(crafter)
        * (1.0 + speed_bonus(machine_effects))
        / recipe.energy_required
    )

    total_per_second = total_per_craft * crafts_per_second

    quality = quality_bonus(machine_effects)

    return (
        round(total_per_craft, 12),
        round(total_per_craft * quality, 12),
        round(total_per_second, 12),
        round(total_per_second * quality, 12),
    )


def _dominates(
    a: tuple[float, ...],
    b: tuple[float, ...],
) -> bool:
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def get_frontier_recipe_candidates(
    recipe: Recipe,
    machine_configurations: Mapping[
        Qualified[Crafter],
        tuple[MachineConfiguration, ...],
    ],
    productivity_research_index: Mapping[Item, int],
) -> tuple[RecipeFrontierCandidate, ...]:

    frontier: list[RecipeFrontierCandidate] = []

    for crafter, configurations in machine_configurations.items():
        for configuration in configurations:
            objectives = calculate_recipe_objectives(
                recipe,
                crafter,
                configuration.effects,
                productivity_research_index,
            )

            if any(
                existing.objectives == objectives
                or _dominates(existing.objectives, objectives)
                for existing in frontier
            ):
                continue

            frontier = [
                existing
                for existing in frontier
                if not _dominates(objectives, existing.objectives)
            ]

            frontier.append(
                RecipeFrontierCandidate(
                    crafter,
                    configuration,
                    objectives,
                )
            )

    return tuple(frontier)


def _legendary_objectives(
    candidate: RecipeFrontierCandidate,
) -> tuple[float, float]:
    return (
        candidate.objectives[0],
        candidate.objectives[2],
    )


def get_legendary_recipe_candidates(
    candidates: tuple[RecipeFrontierCandidate, ...],
) -> tuple[RecipeFrontierCandidate, ...]:
    frontier: list[RecipeFrontierCandidate] = []

    for candidate in candidates:
        objectives = _legendary_objectives(candidate)

        if any(
            (existing.objectives[0], existing.objectives[2]) == objectives
            or _dominates(
                (existing.objectives[0], existing.objectives[2]),
                objectives,
            )
            for existing in frontier
        ):
            continue

        frontier = [
            existing
            for existing in frontier
            if not _dominates(
                objectives,
                (existing.objectives[0], existing.objectives[2]),
            )
        ]

        frontier.append(candidate)

    return tuple(frontier)
