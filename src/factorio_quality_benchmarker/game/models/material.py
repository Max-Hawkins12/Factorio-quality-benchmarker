from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Item:
    name: str


@dataclass(frozen=True, slots=True)
class Fluid:
    name: str


type Material = Item | Fluid


@dataclass(frozen=True, slots=True)
class ItemIngredient:
    item: Item
    amount: float

    @property
    def material(self) -> Material:
        return self.item


@dataclass(frozen=True, slots=True)
class FluidIngredient:
    fluid: Fluid
    amount: float

    @property
    def material(self) -> Material:
        return self.fluid


Ingredient = ItemIngredient | FluidIngredient


@dataclass(frozen=True, slots=True)
class ItemProduct:
    item: Item
    amount: float

    @property
    def material(self) -> Material:
        return self.item


@dataclass(frozen=True, slots=True)
class FluidProduct:
    fluid: Fluid
    amount: float

    @property
    def material(self) -> Material:
        return self.fluid


Product = ItemProduct | FluidProduct
