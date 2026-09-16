from factorio_quality_benchmarker.game.engine import (
    get_frontier_desired_modules,
)
from factorio_quality_benchmarker.optimiser.configurations.machine import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext


def run(simulation: SimulationContext):
    """graphs = generate_recipe_graph_index(
        dict(simulation.materials), dict(simulation.recipes)
    )"""

    beacon = simulation.beacon

    effects = dict(simulation.game_data.module_effects)

    modules = get_frontier_desired_modules(
        tuple(simulation.modules.values()),
        effects,
        simulation.game_data.is_2_1,
    )

    beacon_configuration_cache = BeaconConfigurationCache(
        beacon=beacon,
        modules=modules,
        module_effects=effects,
        is_2_1=simulation.game_data.is_2_1,
    )

    machine_configuration_cache = MachineConfigurationCache(
        modules=modules,
        module_effects=effects,
        is_2_1=simulation.game_data.is_2_1,
        beacon_cache=beacon_configuration_cache,
    )

    recipe_configuration_cache = RecipeConfigurationCache(
        qualities=simulation.qualities,
        crafters=dict(simulation.crafters),
        productivity_research_index=dict(simulation.productivity_research_index),
        machine_cache=machine_configuration_cache,
    )
