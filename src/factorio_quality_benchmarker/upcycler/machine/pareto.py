from typing import TypeVar

from .models import HasMachineEffects, MachineEffects

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


def _deduplicate_configurations[T: HasMachineEffects](
    configurations: tuple[T, ...],
) -> tuple[T, ...]:
    unique: dict[MachineEffects, T] = {}

    for configuration in configurations:
        unique.setdefault(
            configuration.effects,
            configuration,
        )

    return tuple(unique.values())


def get_pareto_frontier[T: HasMachineEffects](
    configurations: tuple[T, ...],
) -> tuple[T, ...]:

    ordered = sorted(
        configurations,
        key=lambda config: (
            -config.effects.speed,
            -config.effects.productivity,
            -config.effects.quality,
        ),
    )

    productivity_values = sorted(
        {configuration.effects.productivity for configuration in ordered},
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

    for configuration in ordered:
        effects = configuration.effects

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
) -> tuple[T, ...]:
    return get_pareto_frontier(_deduplicate_configurations(configurations))
