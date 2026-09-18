from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import Item, Material, Quality


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

    def above(self, quality: Quality) -> QualityAmounts:
        if quality.next is None:
            return QualityAmounts({})

        return QualityAmounts(
            {
                output_quality: amount
                for output_quality, amount in self.amounts.items()
                if output_quality.level > quality.level
            }
        )

    def scale(self, factor: float) -> QualityAmounts:
        return QualityAmounts(
            {quality: amount * factor for quality, amount in self.amounts.items()}
        )

    def __getitem__(self, quality: Quality) -> float:
        return self.amounts.get(quality, 0.0)

    def __add__(self, other: QualityAmounts) -> QualityAmounts:
        return QualityAmounts(
            {
                quality: self[quality] + other[quality]
                for quality in set().union(*[self.amounts.keys(), other.amounts.keys()])
            }
        )

    def __sub__(self, other: QualityAmounts) -> QualityAmounts:
        return QualityAmounts(
            {
                quality: self[quality] - other[quality]
                for quality in set().union(*[self.amounts.keys(), other.amounts.keys()])
            }
        )


@dataclass(frozen=True, slots=True)
class RecipeMetrics:
    quality_bonus: float
    productivity_bonus: float
    crafts_per_second: float

    input_per_craft: Mapping[Material, QualityAmounts]
    input_per_second: Mapping[Material, QualityAmounts]

    output_per_craft: Mapping[Material, QualityAmounts]
    output_per_second: Mapping[Material, QualityAmounts]

    @property
    def input_items_per_craft(self) -> Mapping[Item, QualityAmounts]:
        return {
            item: amounts
            for item, amounts in self.input_per_craft.items()
            if isinstance(item, Item)
        }

    @property
    def total_per_craft(self) -> Mapping[Material, float]:
        return {
            material: round(amount.total, 10)
            for material, amount in self.output_per_craft.items()
        }

    @property
    def total_per_second(self) -> Mapping[Material, float]:
        return {
            material: round(amount.total, 10)
            for material, amount in self.output_per_second.items()
        }

    def total_per_craft_above(self, quality: Quality) -> Mapping[Material, float]:
        return {
            material: round(amount.above(quality).total, 10)
            for material, amount in self.output_per_craft.items()
        }

    def total_per_second_above(self, quality: Quality) -> Mapping[Material, float]:
        return {
            material: round(amount.above(quality).total, 10)
            for material, amount in self.output_per_second.items()
        }


@dataclass(frozen=True, slots=True)
class MinerMetrics:
    output_per_second: QualityAmounts

    @property
    def total_per_second(self) -> float:
        return self.output_per_second.total

    def total_per_second_above(self, quality: Quality) -> float:
        return self.output_per_second.above(quality).total
