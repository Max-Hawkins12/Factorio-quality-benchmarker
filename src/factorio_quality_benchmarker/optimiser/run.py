from factorio_quality_benchmarker.optimiser.configurations.graph.results import (
    optimise_upcycler,
)
from factorio_quality_benchmarker.optimiser.configurations.machine import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.configurations.recipe import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.graphs import (
    generate_recipe_graph_index,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext


def run(simulation: SimulationContext):
    graphs = generate_recipe_graph_index(simulation.materials, simulation.recipes)

    beacon = simulation.beacon

    effects = simulation.game_data.module_effects

    modules = tuple(simulation.modules.values())

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
        crafters=simulation.crafters,
        productivity_research_index=simulation.productivity_research_index,
        machine_cache=machine_configuration_cache,
    )

    iron = simulation.items["iron-plate"]

    optimise_upcycler(
        iron,
        graphs.upcycling_graphs_by_item[iron][2],
        simulation.qualities,
        recipe_configuration_cache,
    )

    """print(len(upcycler_configs))"""
