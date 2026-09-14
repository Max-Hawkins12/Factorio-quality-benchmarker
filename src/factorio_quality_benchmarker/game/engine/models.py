from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import Material, Quality


@dataclass(frozen=True, slots=True)
class MachineEffects:
    speed: float
    productivity: float
    quality: float


@dataclass(frozen=True, slots=True)
class QualityAmounts:
    amounts: Mapping[Quality, float]

    @property
    def total(self) -> float:
        return sum(self.amounts.values())

    def above(self, quality: Quality) -> float:
        if quality.next is None:
            return self.total

        return sum(
            amount
            for output_quality, amount in self.amounts.items()
            if output_quality.level > quality.level
        )

    def __getitem__(self, quality: Quality) -> float:
        return self.amounts.get(quality, 0.0)

    def scale(self, factor: float) -> QualityAmounts:
        return QualityAmounts(
            {quality: amount * factor for quality, amount in self.amounts.items()}
        )


@dataclass(frozen=True, slots=True)
class RecipeMetrics:
    output_per_craft: Mapping[Material, QualityAmounts]
    output_per_second: Mapping[Material, QualityAmounts]

    @property
    def total_per_craft(self) -> Mapping[Material, float]:
        return {
            material: amount.total for material, amount in self.output_per_craft.items()
        }

    @property
    def total_per_second(self) -> Mapping[Material, float]:
        return {
            material: amount.total
            for material, amount in self.output_per_second.items()
        }

    def total_per_craft_above(self, quality: Quality) -> Mapping[Material, float]:
        return {
            material: amount.above(quality)
            for material, amount in self.output_per_craft.items()
        }

    def total_per_second_above(self, quality: Quality) -> Mapping[Material, float]:
        return {
            material: amount.above(quality)
            for material, amount in self.output_per_second.items()
        }


@dataclass(frozen=True, slots=True)
class MinerMetrics:
    output_per_second: QualityAmounts

    @property
    def total_per_second(self) -> float:
        return self.output_per_second.total

    def total_per_second_above(self, quality: Quality) -> float:
        return self.output_per_second.above(quality)
