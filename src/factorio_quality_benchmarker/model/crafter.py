from dataclasses import dataclass

from .common import CraftingCategory, ModuleEffect


@dataclass(frozen=True, slots=True)
class Crafter:
    name: str
    categories: frozenset[CraftingCategory]

    crafting_speed: float
    module_slots: int

    allowed_effects: frozenset[ModuleEffect]

    inherent_productivity: float

    width: int
    height: int
