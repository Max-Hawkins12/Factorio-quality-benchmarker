from collections.abc import Mapping
from dataclasses import dataclass

from factorio_quality_benchmarker.game.engine import QualityAmounts
from factorio_quality_benchmarker.game.models import Item, Recipe
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfiguration,
)
from factorio_quality_benchmarker.optimiser.graphs import RecipeGraph
from factorio_quality_benchmarker.optimiser.simulation import Qualified


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
