from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    Fluid,
    Item,
    Machine,
    Material,
    Miner,
    Module,
    ModuleEffect,
    Quality,
    Recipe,
    Resource,
    Surface,
)


@dataclass(frozen=True, slots=True)
class GameData:
    items: Mapping[str, Item]
    fluids: Mapping[str, Fluid]

    @property
    def materials(self) -> Mapping[str, Material]:
        return {**self.items, **self.fluids}

    recipes: Mapping[str, Recipe]

    crafters: Mapping[str, Crafter]
    miners: Mapping[str, Miner]

    @property
    def machines(self) -> Mapping[str, Machine]:
        return {**self.crafters, **self.miners}

    modules: Mapping[str, Module]
    module_effects: Mapping[str, ModuleEffect]
    beacons: Mapping[str, Beacon]

    resources: Mapping[str, Resource]
    surfaces: Mapping[str, Surface]

    qualities: Mapping[str, Quality]
    metadata: Mapping

    @property
    def factorio_version(self) -> str:
        return self.metadata["metadata"]["factorio_version"]

    @property
    def is_2_1(self) -> bool:
        major, minor, *_ = map(
            int, self.metadata["metadata"]["factorio_version"].split(".")
        )
        return (major, minor) >= (2, 1)

    @property
    def has_space_age(self) -> bool:
        return "Space Age" in self.metadata["metadata"]["active_mods"]
