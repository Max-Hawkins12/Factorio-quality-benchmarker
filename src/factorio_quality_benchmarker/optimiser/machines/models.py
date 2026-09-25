from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.engine import MachineEffects
from factorio_quality_benchmarker.game.models import Module, ModuleEffect
from factorio_quality_benchmarker.optimiser.simulation import Qualified


@dataclass(frozen=True, slots=True)
class ModuleConfiguration:
    modules: tuple[Qualified[Module], ...]
    effects: MachineEffects


@dataclass(frozen=True, slots=True)
class BeaconConfiguration:
    num_beacons: int
    modules: tuple[Qualified[Module], ...]
    effects: MachineEffects


@dataclass(frozen=True, slots=True)
class MachineConfiguration:
    modules: ModuleConfiguration
    beacons: BeaconConfiguration
    effects: MachineEffects


@dataclass(frozen=True, slots=True)
class AllowedRecipeEffects:
    productivity: bool
    quality: bool


@dataclass(frozen=True, slots=True)
class BeaconConfigurationKey:
    allowed_effects: frozenset[ModuleEffect]
    max_beacons: int


type ModuleConfigurationIndex = Mapping[
    AllowedRecipeEffects, tuple[ModuleConfiguration, ...]
]

type MachineConfigurationIndex = Mapping[
    AllowedRecipeEffects, tuple[MachineConfiguration, ...]
]
