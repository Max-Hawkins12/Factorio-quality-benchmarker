from dataclasses import dataclass

from .beacon import Beacon
from .crafting_machine import CraftingMachine
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
    crafting_machines: dict[str, CraftingMachine]
    miners: dict[str, Miner]

    resources: dict[str, Resource]

    modules: dict[str, Module]
    beacons: dict[str, Beacon]

    qualities: dict[str, Quality]
    surfaces: dict[str, Surface]

    factorio_version: str
    has_space_age: bool
