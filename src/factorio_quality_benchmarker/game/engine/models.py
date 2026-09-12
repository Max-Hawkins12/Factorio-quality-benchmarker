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

    def __getitem__(self, quality: Quality) -> float:
        return self.amounts.get(quality, 0.0)

    @property
    def total(self) -> float:
        return sum(self.amounts.values())

    def scale(self, factor: float) -> QualityAmounts:
        return QualityAmounts(
            {quality: amount * factor for quality, amount in self.amounts.items()}
        )


@dataclass(frozen=True, slots=True)
class RecipeMetrics:
    output_per_craft: Mapping[Material, QualityAmounts]
    output_per_second: Mapping[Material, QualityAmounts]
