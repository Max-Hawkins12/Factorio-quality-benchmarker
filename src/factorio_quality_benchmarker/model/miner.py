from dataclasses import dataclass

from .common import ModuleCategory, ModuleEffect, ResourceCategory


@dataclass(frozen=True, slots=True)
class Miner:
    name: str

    resource_categories: frozenset[ResourceCategory]

    mining_speed: float
    module_slots: int

    allowed_effects: frozenset[ModuleEffect]
    allowed_module_categories: frozenset[ModuleCategory]

    maximum_beacons: int
