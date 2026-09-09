from dataclasses import dataclass

from .common import CraftingCategory, ModuleEffect, ResourceCategory


@dataclass(frozen=True, slots=True)
class Crafter:
    name: str
    categories: frozenset[CraftingCategory]

    crafting_speed: float
    inherent_productivity: float

    module_slots: int
    allowed_effects: frozenset[ModuleEffect]
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class Miner:
    name: str
    resource_categories: frozenset[ResourceCategory]

    mining_speed: float

    module_slots: int
    allowed_effects: frozenset[ModuleEffect]
    width: int
    height: int


Machine = Crafter | Miner
