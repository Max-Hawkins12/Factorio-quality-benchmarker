from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    CraftingCategory,
    Fluid,
    Item,
    Material,
    Miner,
    Module,
    ModuleEffect,
    ModuleMachine,
    Quality,
    Recipe,
    Resource,
    ResourceCategory,
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
    def machines(self) -> Mapping[str, ModuleMachine]:
        return self.crafters | self.miners

    modules: dict[str, Module]
    module_effects: dict[str, ModuleEffect]
    beacons: dict[str, Beacon]

    resources: dict[str, Resource]
    surfaces: dict[str, Surface]

    qualities: dict[str, Quality]
    metadata: dict

    best_crafter_by_category: dict[CraftingCategory, Crafter]
    best_miner_by_category: dict[ResourceCategory, Miner]

    @property
    def best_crafters(self) -> dict[str, Crafter]:
        return {
            crafter.name: crafter for crafter in self.best_crafter_by_category.values()
        }

    @property
    def best_miners(self) -> dict[str, Miner]:
        return {miner.name: miner for miner in self.best_miner_by_category.values()}

    @property
    def best_machines(self) -> Mapping[str, ModuleMachine]:
        return self.best_crafters | self.best_miners

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
