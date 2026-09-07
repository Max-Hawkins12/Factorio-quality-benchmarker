from dataclasses import dataclass

from .common import ModuleEffect, ResourceCategory


@dataclass(frozen=True, slots=True)
class Miner:
    name: str

    resource_categories: frozenset[ResourceCategory]

    mining_speed: float
    module_slots: int

    allowed_effects: frozenset[ModuleEffect]

    width: int
    height: int
