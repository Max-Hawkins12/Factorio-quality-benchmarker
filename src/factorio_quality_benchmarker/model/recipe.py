from dataclasses import dataclass

from .common import CraftingCategory
from .material import Ingredient, Product


@dataclass(frozen=True, slots=True)
class SurfaceCondition:
    property: str
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
    maximum_productivity: float

    surface_conditions: tuple[SurfaceCondition, ...]
