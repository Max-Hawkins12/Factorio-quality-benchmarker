from typing import TypeVar

from .models import HasMachineEffects, MachineEffects, RecipeEffects

T = TypeVar("T")


class MaxFenwickTree:
    def __init__(self, size: int) -> None:
        self.tree = [float("-inf")] * (size + 1)

    def update(self, index: int, value: float) -> None:
        while index < len(self.tree):
            self.tree[index] = max(
                self.tree[index],
                value,
            )
            index += index & -index

    def query(self, index: int) -> float:
        maximum = float("-inf")

        while index > 0:
            maximum = max(
                maximum,
                self.tree[index],
            )
            index -= index & -index

        return maximum


def _get_pareto_effects(
    effects: MachineEffects,
    recipe_effects: RecipeEffects,
) -> MachineEffects:
    return MachineEffects(
        speed=effects.speed,
        productivity=(effects.productivity if recipe_effects.productivity else 0.0),
        quality=(effects.quality if recipe_effects.quality else 0.0),
    )


def _deduplicate_configurations[T: HasMachineEffects](
    configurations: tuple[T, ...],
    recipe_effects: RecipeEffects,
) -> tuple[T, ...]:
    unique: dict[MachineEffects, T] = {}

    for configuration in configurations:
        effects = _get_pareto_effects(
            configuration.effects,
            recipe_effects,
        )

        unique.setdefault(effects, configuration)

    return tuple(unique.values())


def get_pareto_frontier[T: HasMachineEffects](
    configurations: tuple[T, ...],
    recipe_effects: RecipeEffects,
) -> tuple[T, ...]:

    configurations_with_effects = tuple(
        (
            configuration,
            _get_pareto_effects(
                configuration.effects,
                recipe_effects,
            ),
        )
        for configuration in configurations
    )

    ordered = sorted(
        configurations_with_effects,
        key=lambda value: (
            -value[1].speed,
            -value[1].productivity,
            -value[1].quality,
        ),
    )

    productivity_values = sorted(
        {effects.productivity for _, effects in ordered},
        reverse=True,
    )

    productivity_index = {
        productivity: index
        for index, productivity in enumerate(
            productivity_values,
            start=1,
        )
    }

    tree = MaxFenwickTree(len(productivity_values))

    frontier: list[T] = []

    for configuration, effects in ordered:
        index = productivity_index[effects.productivity]

        best_quality = tree.query(index)

        if best_quality >= effects.quality:
            continue

        frontier.append(configuration)

        tree.update(
            index,
            effects.quality,
        )

    return tuple(frontier)


def get_unique_pareto_frontier[T: HasMachineEffects](
    configurations: tuple[T, ...],
    recipe_effects: RecipeEffects,
) -> tuple[T, ...]:
    return get_pareto_frontier(
        _deduplicate_configurations(
            configurations,
            recipe_effects,
        ),
        recipe_effects,
    )
