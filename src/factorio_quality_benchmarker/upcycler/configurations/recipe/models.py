from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import Machine, Recipe
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    MachineConfiguration,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified


@dataclass(frozen=True, slots=True)
class RecipeMetrics:
    output_per_second: float
    output_per_craft: float
    quality_output_per_second: float
    quality_output_per_craft: float


@dataclass(frozen=True, slots=True)
class RecipeConfiguration:
    recipe: Recipe
    machine: Qualified[Machine]

    machine_configuration: MachineConfiguration

    mertics: RecipeMetrics
