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


type QualifiedIndex[T] = Mapping[Quality, Mapping[str, T]]

type QualifiedMachine = Qualified[Crafter] | Qualified[Miner]


@dataclass(frozen=True, slots=True)
class SimulationData:
    game_data: GameData

    crafters_by_quality: QualifiedIndex[Qualified[Crafter]]
    miners_by_quality: QualifiedIndex[Qualified[Miner]]
    modules_by_quality: QualifiedIndex[Qualified[Module]]
    beacons_by_quality: QualifiedIndex[Qualified[Beacon]]

    @property
    def machines_by_quality(self) -> QualifiedIndex[QualifiedMachine]:
        return {
            quality: {
                **self.crafters_by_quality[quality],
                **self.miners_by_quality[quality],
            }
            for quality in self.game_data.qualities.values()
        }
