from dataclasses import dataclass

from .beacon import Beacon
from .crafter import Crafter
from .material import Fluid, Item
from .miner import Miner
from .module import Module
from .quality import Quality
from .recipe import Recipe
from .resource import Resource
from .surface import Surface


@dataclass(frozen=True, slots=True)
class GameData:
    items: dict[str, Item]
    fluids: dict[str, Fluid]

    recipes: dict[str, Recipe]
    crafters: dict[str, Crafter]
    miners: dict[str, Miner]

    resources: dict[str, Resource]

    modules: dict[str, Module]
    beacons: dict[str, Beacon]

    qualities: dict[str, Quality]
    surfaces: dict[str, Surface]

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
