from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass

import networkx as nx

from factorio_quality_benchmarker.game.models import (
    Fluid,
    Item,
    Material,
    Recipe,
)


@dataclass(frozen=True, slots=True)
class RecipeGraph(ABC):
    """
    Base class for all graph structures used by the upcycler system.
    """

    graph: nx.DiGraph
    start_recipe: Recipe
    end_recipe: Recipe

    @property
    def input_materials(self) -> tuple[Material, ...]:
        """Materials consumed by the graph's start recipe."""
        return self.start_recipe.ingredient_materials

    @property
    def input_items(self) -> tuple[Item, ...]:
        """Item inputs consumed by the graph's start recipe."""
        return self.start_recipe.ingredient_items

    @property
    def output_items(self) -> tuple[Item, ...]:
        """Items produced by the end recipe of the graph"""
        return self.end_recipe.product_items

    @property
    def required_fluids(self) -> tuple[Fluid, ...]:
        """Unique fluids consumed by recipes anywhere in the graph."""
        fluids: set[Fluid] = set()

        for node in self.graph.nodes:
            if isinstance(node, Recipe):
                fluids.update(node.ingredient_fluids)

        return tuple(fluids)

    @property
    def produced_fluids(self) -> tuple[Fluid, ...]:
        fluids: set[Fluid] = set()

        for node in self.graph.nodes:
            if isinstance(node, Recipe):
                fluids.update(node.product_fluids)

        return tuple(fluids)

    @classmethod
    @abstractmethod
    def is_valid(
        cls,
        graph: nx.DiGraph,
        start_recipe: Recipe,
        end_recipe: Recipe,
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class UpcyclingGraph(RecipeGraph):
    """
    A core upcycling graph which consists of a closed cycle
    """

    @property
    def intermediate_upcycled_item(self) -> Item | None:
        """
        Return if there is an intermediate item craft in this upcyling graph
        """
        item_nodes = [node for node in self.graph.nodes if isinstance(node, Item)]

        for item_node in item_nodes:
            if any(
                isinstance(predecessor, Recipe) and not predecessor.is_recycling
                for predecessor in self.graph.predecessors(item_node)
            ) and any(
                isinstance(successor, Recipe) and successor.is_recycling
                for successor in self.graph.successors(item_node)
            ):
                return item_node

        return None

    @classmethod
    def is_valid(
        cls,
        graph: nx.DiGraph,
        start_recipe: Recipe,
        end_recipe: Recipe,
    ) -> bool:
        return start_recipe.ingredient_items == end_recipe.product_items


@dataclass(frozen=True, slots=True)
class ProductionGraph(RecipeGraph):
    """
    A graph of a recipe production chain
    """

    @classmethod
    def is_valid(
        cls,
        graph: nx.DiGraph,
        start_recipe: Recipe,
        end_recipe: Recipe,
    ) -> bool:

        current_recipe = start_recipe

        while current_recipe != end_recipe:
            products = tuple(graph.successors(current_recipe))

            next_recipes: set[Recipe] = set()

            for product in products:
                consumers = tuple(graph.successors(product))

                if len(consumers) != 1:
                    return False

                next_recipes.add(consumers[0])

            if len(next_recipes) != 1:
                return False

            current_recipe = next_recipes.pop()

        return True


@dataclass(frozen=True, slots=True)
class RecipeGraphIndex:
    upcycling_graphs_by_item: Mapping[Item, tuple[UpcyclingGraph, ...]]
    production_graphs_by_item: Mapping[Item, tuple[ProductionGraph, ...]]
