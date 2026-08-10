from dataclasses import dataclass

from . import CraftingCategory, Ingredient


@dataclass(frozen=True, slots=True)
class SurfaceCondtion:
    property: str
    minimum: float | None = None
    maximim: float | None = None


@dataclass(frozen=True, slots=True)
class Recipe:
    name: str
    categories: frozenset[CraftingCategory]
    ingredients: tuple[Ingredient, ...]
    results: tuple[Ingredient, ...]

    allow_productivity: bool
    allow_quality: bool

    surface_conditions: tuple[SurfaceCondtion, ...]
