from dataclasses import dataclass

from .common import CraftingCategory, ModuleCategory, ModuleEffect


@dataclass(frozen=True, slots=True)
class CraftingMachine:
    name: str
    categories: frozenset[CraftingCategory]

    crafting_speed: float
    module_slots: int

    allowed_effects: frozenset[ModuleEffect]
    allowed_module_categories: frozenset[ModuleCategory]

    inherent_productivity: float

    maximum_beacons: int
