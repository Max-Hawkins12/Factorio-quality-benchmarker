from dataclasses import dataclass

from factorio_quality_benchmarker.game.engine import RecipeMetrics
from factorio_quality_benchmarker.game.models import Crafter
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    MachineConfiguration,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified


@dataclass(frozen=True, slots=True)
class RecipeConfiguration:
    crafter: Qualified[Crafter]
    machine_configuration: MachineConfiguration

    metrics: RecipeMetrics
