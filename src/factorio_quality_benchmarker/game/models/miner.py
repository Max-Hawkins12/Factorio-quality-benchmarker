from dataclasses import dataclass

from .common import ModuleMachine, ResourceCategory


@dataclass(frozen=True, slots=True)
class Miner(ModuleMachine):
    name: str
    resource_categories: frozenset[ResourceCategory]

    mining_speed: float
