from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass

import networkx as nx

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Fluid, Item, Material, Recipe
from factorio_quality_benchmarker.optimiser.recipes import RecipeConfiguration
from factorio_quality_benchmarker.optimiser.simulation import Qualified


@dataclass(frozen=True, slots=True)
class RecipeGraph(ABC):
    """
    Base class for all graph structures used by the upcycler system.
    """

    graph: nx.DiGraph
    start_recipe: Recipe
    end_recipe: Recipe

    @property
    def ordered_recipes(self) -> tuple[Recipe, ...]:
        graph = self.graph.copy()

        graph.remove_edges_from(
            (self.end_recipe, successor)
            for successor in tuple(graph.successors(self.end_recipe))
        )

        return tuple(
            node for node in nx.topological_sort(graph) if isinstance(node, Recipe)
        )

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
    def recycled_item(self) -> Item:
        """
        Return the item consumed by the recycling recipe.
        """
        recycling_ingredients = self.end_recipe.ingredient_items

        if len(recycling_ingredients) != 1:
            raise ValueError(
                f"Expected recycling recipe to have exactly one item input, got {len(recycling_ingredients)}"
            )

        return recycling_ingredients[0]

    @property
    def is_self_recycling(self) -> bool:
        return self.start_recipe is self.end_recipe

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
class UpcyclerSystem:
    upcycler: UpcyclingGraph
    production_graph: ProductionGraph | None = None


@dataclass(frozen=True, slots=True)
class GraphMetrics:
    legendary_per_input: float
    legendary_per_second: float


@dataclass(frozen=True, slots=True)
class GraphConfiguration:
    recipe_configurations: Mapping[Qualified[Recipe], RecipeConfiguration]
    metrics: GraphMetrics


@dataclass(frozen=True, slots=True)
class GraphResult:
    graph: RecipeGraph
    best_per_input: GraphConfiguration
    best_per_second: GraphConfiguration


@dataclass(frozen=True, slots=True)
class UpcyclingResult:
    upcyclers: tuple[GraphResult, ...]
    production_graphs: tuple[GraphResult, ...]


@dataclass(slots=True)
class GraphState:
    available: dict[Item, QualityAmounts]
    configurations: dict[Qualified[Recipe], RecipeConfiguration]
