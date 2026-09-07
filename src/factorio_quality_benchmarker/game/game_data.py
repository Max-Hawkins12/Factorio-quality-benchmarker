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

    resources: dict[str, Resource]

    modules: dict[str, Module]
    beacons: dict[str, Beacon]

    qualities: dict[str, Quality]
    surfaces: dict[str, Surface]

    metadata: dict

    best_crafter_by_category: dict[CraftingCategory, Crafter]
    best_miner_by_category: dict[ResourceCategory, Miner]

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
