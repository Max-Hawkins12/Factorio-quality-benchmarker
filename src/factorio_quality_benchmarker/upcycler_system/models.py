from collections.abc import Mapping
from dataclasses import dataclass

import networkx as nx

from factorio_quality_benchmarker.model import (
    Item,
    Material,
    Recipe,
)


@dataclass(frozen=True, slots=True)
class RecipeIndex:
    crafter_producers_by_material: Mapping[Material, tuple[Recipe, ...]]
    crafter_consumers_by_material: Mapping[Material, tuple[Recipe, ...]]
    recycler_producers_by_material: Mapping[Material, tuple[Recipe, ...]]
    recycler_consumers_by_material: Mapping[Material, Recipe]


@dataclass(frozen=True, slots=True)
class UpcyclerGraph:
    graph: nx.DiGraph
    start_recipe: Recipe
    input_materials: tuple[Material, ...]

    @property
    def input_items(self) -> tuple[Item, ...]:
        return tuple(item for item in self.input_materials if isinstance(item, Item))


@dataclass(frozen=True, slots=True)
class UpcyclerSystem:
    target: Item
    upcyclers: tuple[UpcyclerGraph, ...]
