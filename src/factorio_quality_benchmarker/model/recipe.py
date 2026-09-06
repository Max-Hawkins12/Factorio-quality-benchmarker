from dataclasses import dataclass

from .common import CraftingCategory, SurfaceProperty
from .material import (
    Fluid,
    FluidIngredient,
    FluidProduct,
    Ingredient,
    Item,
    ItemIngredient,
    ItemProduct,
    Material,
    Product,
)


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

    @property
    def is_recycling(self):
        return any(category.name == "recycling" for category in self.categories)

    @property
    def ingredient_materials(self) -> tuple[Material, ...]:
        return tuple(ingredient.material for ingredient in self.ingredients)

    @property
    def ingredient_items(self) -> tuple[Item, ...]:
        return tuple(
            ingredient.item
            for ingredient in self.ingredients
            if isinstance(ingredient, ItemIngredient)
        )

    @property
    def ingredient_fluids(self) -> tuple[Fluid, ...]:
        return tuple(
            ingredient.fluid
            for ingredient in self.ingredients
            if isinstance(ingredient, FluidIngredient)
        )

    @property
    def product_materials(self) -> tuple[Material, ...]:
        return tuple(ingredient.material for ingredient in self.products)

    @property
    def product_items(self) -> tuple[Item, ...]:
        return tuple(
            ingredient.item
            for ingredient in self.products
            if isinstance(ingredient, ItemProduct)
        )

    @property
    def product_fluids(self) -> tuple[Fluid, ...]:
        return tuple(
            ingredient.fluid
            for ingredient in self.products
            if isinstance(ingredient, FluidProduct)
        )
