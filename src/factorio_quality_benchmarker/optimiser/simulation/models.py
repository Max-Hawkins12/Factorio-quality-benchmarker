from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from factorio_quality_benchmarker.game import GameData
from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    Fluid,
    Item,
    Material,
    Miner,
    Module,
    Quality,
    Recipe,
    Resource,
    Surface,
)


# Model for an entity with a quality
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


# Configurable simulation runtime settings
@dataclass(frozen=True, slots=True)
class ProductivityResearchLevels:
    processing_unit_level: int
    low_density_structure_level: int
    steel_level: int
    plastic_bar_level: int
    rocket_fuel_level: int

    def validate_level(self, level):
        if level < 0 or level > 30:
            raise ValueError("Productivity research levels must be between 0 and 30")

    def __post_init__(self):
        self.validate_level(self.processing_unit_level)
        self.validate_level(self.low_density_structure_level)
        self.validate_level(self.steel_level)
        self.validate_level(self.plastic_bar_level)
        self.validate_level(self.rocket_fuel_level)


class UpcyclerScope(StrEnum):
    CURATED = "curated"
    ESSENTIALS = "essentials"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class RunConfig:
    productivity_levels: ProductivityResearchLevels
    upcycler_scope: UpcyclerScope

    entity_quality: Quality


@dataclass(frozen=True, slots=True)
class SimulationContext:
    game_data: GameData
    run_config: RunConfig

    productivity_research_index: Mapping[Item, int]

    # Index entities by all quality versions
    items_by_quality: QualifiedIndex[Qualified[Item]]
    crafters_by_quality: QualifiedIndex[Qualified[Crafter]]
    miners_by_quality: QualifiedIndex[Qualified[Miner]]
    modules_by_quality: QualifiedIndex[Qualified[Module]]
    beacons_by_quality: QualifiedIndex[Qualified[Beacon]]

    @property
    def producer_recipes_by_material(self) -> Mapping[Material, tuple[Recipe, ...]]:
        producer_recipes: dict[Material, list[Recipe]] = {
            material: [] for material in self.materials.values()
        }

        for recipe in self.recipes.values():
            for material in recipe.product_materials:
                producer_recipes[material].append(recipe)

        return {
            material: tuple(recipe) for material, recipe in producer_recipes.items()
        }

    @property
    def recycling_recipes_by_item(self) -> Mapping[Item, Recipe]:
        recycling_recipes: dict[Item, Recipe] = {}

        for recipe in self.recipes.values():
            if recipe.is_recycling:
                recycling_recipes[recipe.ingredient_items[0]] = recipe

        return recycling_recipes

    def item_recycling_recipe(self, item: Item) -> Recipe:
        for recipe in self.producer_recipes_by_material[item]:
            if recipe.is_recycling:
                return recipe
        raise ValueError(f"{item.name} has no recorded recycling recipe.")

    # "Overrides" of the parsed game data values
    items: Mapping[str, Item]
    recipes: Mapping[str, Recipe]

    @property
    def fluids(self) -> Mapping[str, Fluid]:
        return self.game_data.fluids

    @property
    def materials(self) -> Mapping[str, Material]:
        return {**self.items, **self.fluids}

    @property
    def crafters(self) -> Mapping[str, Qualified[Crafter]]:
        return self.crafters_by_quality[self.run_config.entity_quality]

    @property
    def miners(self) -> Mapping[str, Qualified[Miner]]:
        return self.miners_by_quality[self.run_config.entity_quality]

    @property
    def machines(self) -> Mapping[str, QualifiedMachine]:
        return {**self.crafters, **self.miners}

    @property
    def modules(self) -> Mapping[str, Qualified[Module]]:
        return self.modules_by_quality[self.run_config.entity_quality]

    @property
    def beacon(self) -> Qualified[Beacon]:
        return self.beacons_by_quality[self.run_config.entity_quality]["beacon"]

    @property
    def resources(self) -> Mapping[str, Resource]:
        return self.game_data.resources

    @property
    def qualities(self) -> Mapping[str, Quality]:
        return self.game_data.qualities

    @property
    def surfaces(self) -> Mapping[str, Surface]:
        return self.game_data.surfaces
