from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    name: str


@dataclass(frozen=True, slots=True)
class Fluid:
    name: str


@dataclass(frozen=True, slots=True)
class ItemIngredient:
    item: Item
    amount: float


@dataclass(frozen=True, slots=True)
class FluidIngredient:
    fluid: Fluid
    amount: float


@dataclass(frozen=True, slots=True)
class ItemProduct:
    item: Item
    amount: float


@dataclass(frozen=True, slots=True)
class FluidProduct:
    fluid: Fluid
    amount: float


Material = Item | Fluid
Ingredient = ItemIngredient | FluidIngredient
Product = ItemProduct | FluidProduct
