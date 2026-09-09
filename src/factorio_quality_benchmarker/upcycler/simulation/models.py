from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from factorio_quality_benchmarker.game import GameData
from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    Miner,
    Module,
    Quality,
)


class Named(Protocol):
    @property
    def name(self) -> str: ...


@dataclass(frozen=True, slots=True)
class Qualified[T: Named]:
    entity: T
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.entity.name}"


type QualifiedIndex[T: Named] = Mapping[Quality, Mapping[str, Qualified[T]]]


@dataclass(frozen=True, slots=True)
class SimulationData:
    game_data: GameData

    crafters_by_quality: QualifiedIndex[Crafter]
    miners_by_quality: QualifiedIndex[Miner]
    modules_by_quality: QualifiedIndex[Module]
    beacons_by_quality: QualifiedIndex[Beacon]
