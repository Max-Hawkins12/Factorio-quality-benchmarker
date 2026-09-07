from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import Module


@dataclass(frozen=True, slots=True)
class ModuleConfiguration:
    modules: tuple[Module, ...]


@dataclass(frozen=True, slots=True)
class BeaconConfiguration:
    beacons: tuple[ModuleConfiguration, ...]

    @property
    def beacon_count(self) -> int:
        return len(self.beacons)


@dataclass(frozen=True, slots=True)
class MachineConfiguration:
    modules: ModuleConfiguration
    beacons: BeaconConfiguration
