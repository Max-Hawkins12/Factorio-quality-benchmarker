from factorio_quality_benchmarker.optimiser.graphs import (
    UpcyclerResultsCache,
    UpcyclerSystemCache,
)
from factorio_quality_benchmarker.optimiser.machines import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext


def run(simulation: SimulationContext):

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
        upcycler_systems_cache=UpcyclerSystemCache(
            producer_recipes=simulation.producer_recipes_by_material,
            recycling_recipes=simulation.recycling_recipes_by_item,
        ),
    )
