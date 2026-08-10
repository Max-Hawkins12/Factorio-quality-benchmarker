from dataclasses import dataclass

from .common import CraftingCategory


@dataclass(frozen=True, slots=True)
class CraftingMachine:
    name: str
    categories: frozenset[CraftingCategory]

    crafting_speed: float
    module_slots: int
    allowed_modules: list  # List of module types

    inherent_productivity: float

    maximum_beacons: int
