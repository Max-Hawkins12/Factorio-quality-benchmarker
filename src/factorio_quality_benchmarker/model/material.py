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


Ingredient = ItemIngredient | FluidIngredient
Material = Item | Fluid
