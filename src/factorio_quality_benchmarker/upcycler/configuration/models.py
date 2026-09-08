from dataclasses import dataclass
from typing import Protocol

from factorio_quality_benchmarker.game.models import Module


@dataclass(frozen=True, slots=True)
class ModuleConfiguration:
    modules: tuple[Module, ...]


@dataclass(frozen=True, slots=True)
class BeaconConfiguration:
    num_beacons: int
    modules: ModuleConfiguration


@dataclass(frozen=True, slots=True)
class MachineConfiguration:
    modules: ModuleConfiguration
    beacons: BeaconConfiguration


@dataclass(frozen=True, slots=True)
class MachineEffects:
    speed: float
    productivity: float
    quality: float


@dataclass(frozen=True, slots=True)
class EffectiveModuleConfiguration:
    configuration: ModuleConfiguration
    effects: MachineEffects


@dataclass(frozen=True, slots=True)
class EffectiveBeaconConfiguration:
    configuration: BeaconConfiguration
    effects: MachineEffects


@dataclass(frozen=True, slots=True)
class EffectiveMachineConfiguration:
    configuration: MachineConfiguration
    effects: MachineEffects


class HasMachineEffects(Protocol):
    @property
    def effects(self) -> MachineEffects: ...
