from dataclasses import dataclass

from .beacon import Beacon
from .crafter import Crafter
from .material import Item
from .miner import Miner
from .module import Module
from .quality import Quality


@dataclass(frozen=True, slots=True)
class QualifiedItem:
    item: Item
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.item.name}"


@dataclass(frozen=True, slots=True)
class QualifiedCrafter:
    machine: Crafter
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.machine.name}"


@dataclass(frozen=True, slots=True)
class QualifiedMiner:
    machine: Miner
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.machine.name}"


@dataclass(frozen=True, slots=True)
class QualifiedModule:
    module: Module
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.module.name}"


@dataclass(frozen=True, slots=True)
class QualifiedBeacon:
    beacon: Beacon
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.beacon.name}"


@dataclass(frozen=True, slots=True)
class BeaconConfiguration:
    beacon: QualifiedBeacon
    modules: tuple[QualifiedModule, ...]


@dataclass(frozen=True, slots=True)
class CrafterConfiguration:
    machine: QualifiedCrafter
    modules: tuple[QualifiedModule, ...]
    beacons: tuple[BeaconConfiguration, ...]


@dataclass(frozen=True, slots=True)
class MinerConfiguration:
    miner: QualifiedMiner
    modules: tuple[QualifiedModule, ...]
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
