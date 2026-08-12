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
    crafter: Crafter
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.crafter.name}"


@dataclass(frozen=True, slots=True)
class QualifiedMiner:
    miner: Miner
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.miner.name}"


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
