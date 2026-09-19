from factorio_quality_benchmarker.optimiser.graphs import RecipeGraphCache
from factorio_quality_benchmarker.optimiser.machines import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext


def run(simulation: SimulationContext):
    recipe_graph_cache = RecipeGraphCache(
        producer_recipes=simulation.producer_recipes_by_material,
        recycling_recipes=simulation.recycling_recipes_by_item,
    )

    em_plants = recipe_graph_cache.get(simulation.items["electromagnetic-plant"])

    print(len(em_plants))
    print([node.name for graph in em_plants for node in graph.graph.nodes])

    recipe_graph_cache.get(simulation.items["holmium-plate"])
    recipe_graph_cache.get(simulation.items["steel-plate"])

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

    """iron = simulation.items["iron-plate"]

    generate_graph_results(
        iron,
        graphs.upcycling_graphs_by_item[iron][0],
        simulation.qualities,
        recipe_configuration_cache,
    )"""
