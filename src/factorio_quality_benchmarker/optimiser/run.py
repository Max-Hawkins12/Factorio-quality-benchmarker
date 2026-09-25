from factorio_quality_benchmarker.optimiser.machines import (
    BeaconConfigurationCache,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.recipes import (
    RecipeConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import SimulationContext
from factorio_quality_benchmarker.optimiser.upcyclers import (
    UpcyclerResultsCache,
    UpcyclerSystemCache,
)


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
        upcycler_system_cache=UpcyclerSystemCache(
            producer_recipes=simulation.producer_recipes_by_material,
            recycling_recipes=simulation.recycling_recipes_by_item,
        ),
    )

    holmium_results = upcycler_results_cache.get(simulation.items["tungsten-plate"])

    print(f"Total Results: {len(holmium_results)}")

    for result in holmium_results:
        print(f"Input Items: {[item.name for item in result.system.input_materials]}")
        print(f"Output Items: {[item.name for item in result.system.output_items]}")

        print(
            f"Best Legendary/Input: {result.per_input.legendary_per_input.legendary_output} has Legendary/Second {result.per_input.legendary_per_second.legendary_output}"
        )
        """for recipe, config in result.per_input.configuration.configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )"""

        print(
            f"Best Legendary/Second: {result.per_second.legendary_per_second.legendary_output} has Legendary/Input {result.per_second.legendary_per_input.legendary_output}"
        )
        """for recipe, config in result.per_second.configuration.configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )"""

        print()

    holmium_results = upcycler_results_cache.get(simulation.items["holmium-plate"])

    print(f"Total Results: {len(holmium_results)}")

    for result in holmium_results:
        print(f"Input Items: {[item.name for item in result.system.input_materials]}")
        print(f"Output Items: {[item.name for item in result.system.output_items]}")

        print(
            f"Best Legendary/Input: {result.per_input.legendary_per_input.legendary_output} has Legendary/Second {result.per_input.legendary_per_second.legendary_output}"
        )
        """for recipe, config in result.per_input.configuration.configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )"""

        print(
            f"Best Legendary/Second: {result.per_second.legendary_per_second.legendary_output} has Legendary/Input {result.per_second.legendary_per_input.legendary_output}"
        )
        """for recipe, config in result.per_second.configuration.configurations.items():
            print(f"Recipe: {recipe.name}")
            print(
                f"Config: Modules: {[module.name for module in config.machine_configuration.modules.modules]} Beacons: {[module.name for module in config.machine_configuration.beacons.modules]}"
            )"""

        print()
