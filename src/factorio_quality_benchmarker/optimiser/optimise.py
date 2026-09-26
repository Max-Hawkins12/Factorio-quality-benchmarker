import logging
from collections.abc import Mapping

from factorio_quality_benchmarker.game.models import Item
from factorio_quality_benchmarker.optimiser.machines import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.recipes import RecipeConfigurationCache
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext
from factorio_quality_benchmarker.optimiser.upcyclers import (
    UpcyclerResult,
    UpcyclerResultsCache,
    UpcyclerSystemCache,
)

logger = logging.getLogger(__name__)


def optimise(
    simulation: SimulationContext,
    items: tuple[Item, ...],
) -> Mapping[Item, set[UpcyclerResult]]:

    upcycler_results_cache = UpcyclerResultsCache(
        qualities=simulation.qualities,
        recipe_cache=RecipeConfigurationCache(
            qualities=simulation.qualities,
            crafters=simulation.crafters,
            productivity_research_index=simulation.productivity_research_index,
            machine_cache=MachineConfigurationCache(
                modules=tuple(simulation.modules.values()),
                module_effects=simulation.game_data.module_effects,
                is_2_1=simulation.game_data.is_2_1,
                beacon_cache=BeaconConfigurationCache(
                    beacon=simulation.beacon,
                    modules=tuple(simulation.modules.values()),
                    module_effects=simulation.game_data.module_effects,
                    is_2_1=simulation.game_data.is_2_1,
                ),
            ),
        ),
        upcycler_system_cache=UpcyclerSystemCache(
            producer_recipes=simulation.producer_recipes_by_material,
            recycling_recipes=simulation.recycling_recipes_by_item,
        ),
    )

    for item in items:
        logger.info("Optimising upcycler systems for %s", item.name)
        logger.info(
            "Found optimal configurations for %d upcycler systems of %s",
            len(upcycler_results_cache.get(item)),
            item.name,
        )

    return upcycler_results_cache.all_results
