from factorio_quality_benchmarker.optimiser.graphs import UpcyclerSystemCache
from factorio_quality_benchmarker.optimiser.machines import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext


def run(simulation: SimulationContext):

    beacon_configuration_cache = BeaconConfigurationCache(
        beacon=simulation.beacon,
        modules=tuple(simulation.modules.values()),
        module_effects=simulation.game_data.module_effects,
        is_2_1=simulation.game_data.is_2_1,
    )

    machine_configuration_cache = MachineConfigurationCache(
        modules=tuple(simulation.modules.values()),
        module_effects=simulation.game_data.module_effects,
        is_2_1=simulation.game_data.is_2_1,
        beacon_cache=beacon_configuration_cache,
    )

    recipe_configuration_cache = RecipeConfigurationCache(
        qualities=simulation.qualities,
        crafters=simulation.crafters,
        productivity_research_index=simulation.productivity_research_index,
        machine_cache=machine_configuration_cache,
    )

    recipe_graph_cache = UpcyclerSystemCache(
        producer_recipes=simulation.producer_recipes_by_material,
        recycling_recipes=simulation.recycling_recipes_by_item,
    )

    """len(recipe_graph_cache.get_upcycler_systems(simulation.items["steel-plate"]))
    len(recipe_graph_cache.get_upcycler_systems(simulation.items["holmium-plate"]))
    len(recipe_graph_cache.get_upcycler_systems(simulation.items["electronic-circuit"]))
    len(recipe_graph_cache.get_upcycler_systems(simulation.items["foundry"]))
    len(recipe_graph_cache.get_upcycler_systems(simulation.items["tungsten-plate"]))"""
    print(
        f"Iron Plate: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['iron-plate']))}"
    )
    print(
        f"Holmium Plate: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['holmium-plate']))}"
    )
    print(
        f"Steel Plate: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['steel-plate']))}"
    )
    print(
        f"Electronic Circuit: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['electronic-circuit']))}"
    )
    print(
        f"Foundry: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['foundry']))}"
    )
    print(
        f"Tungsten Plate: {len(recipe_graph_cache.get_upcycler_systems(simulation.items['tungsten-plate']))}"
    )

    """generate_graph_results(
        iron,
        iron_graphs[0].upcycler,
        simulation.qualities,
        recipe_configuration_cache,
    )"""
