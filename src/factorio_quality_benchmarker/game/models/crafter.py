from dataclasses import dataclass

from .common import CraftingCategory, ModuleMachine


@dataclass(frozen=True, slots=True)
class Crafter(ModuleMachine):
    name: str
    categories: frozenset[CraftingCategory]

    crafting_speed: float
    inherent_productivity: float
