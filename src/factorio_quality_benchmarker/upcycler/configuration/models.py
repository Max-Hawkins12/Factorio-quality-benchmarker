from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import Beacon, Crafter, Miner, Module
from factorio_quality_benchmarker.upcycler.simulation import Qualified


@dataclass(frozen=True, slots=True)
class BeaconConfiguration:
    beacon: Qualified[Beacon]
    modules: tuple[Qualified[Module], ...]


@dataclass(frozen=True, slots=True)
class CrafterConfiguration:
    machine: Qualified[Crafter]
    modules: tuple[Qualified[Module], ...]
    beacons: tuple[BeaconConfiguration, ...]


@dataclass(frozen=True, slots=True)
class MinerConfiguration:
    miner: Qualified[Miner]
    modules: tuple[Qualified[Module], ...]
    beacons: tuple[BeaconConfiguration, ...]


@dataclass(frozen=True, slots=True)
class EffectiveCrafterStats:
    crafting_speed: float
    productivity: float
    quality: float


@dataclass(frozen=True, slots=True)
class EffectiveMinerStats:
    crafting_speed: float
    productivity: float
    quality: float
