from dataclasses import dataclass

from .common import CraftingCategory, SurfaceProperty
from .material import Ingredient, Product


@dataclass(frozen=True, slots=True)
class SurfaceCondition:
    property: SurfaceProperty
    minimum: float | None = None
    maximum: float | None = None


@dataclass(frozen=True, slots=True)
class Recipe:
    name: str
    categories: frozenset[CraftingCategory]
    ingredients: tuple[Ingredient, ...]
    products: tuple[Product, ...]

    energy_required: float

    allow_productivity: bool
    allow_quality: bool

    surface_conditions: tuple[SurfaceCondition, ...]
