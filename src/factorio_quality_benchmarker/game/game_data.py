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
    items: dict[str, Item]
    fluids: dict[str, Fluid]

    @property
    def materials(self) -> dict[str, Material]:
        return self.items | self.fluids

    recipes: dict[str, Recipe]

    crafters: dict[str, Crafter]
    miners: dict[str, Miner]

    @property
    def machines(self) -> dict[str, Machine]:
        return self.crafters | self.miners

    modules: dict[str, Module]
    module_effects: dict[str, ModuleEffect]
    beacons: dict[str, Beacon]

    resources: dict[str, Resource]
    surfaces: dict[str, Surface]

    qualities: dict[str, Quality]
    metadata: dict

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
