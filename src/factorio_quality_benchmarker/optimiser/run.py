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
from factorio_quality_benchmarker.optimiser.upcyclers.models import UpcyclerResult


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

    print_result(
        upcycler_results_cache.get(simulation.items["tungsten-plate"]), "tungsten-plate"
    )

    print_result(
        upcycler_results_cache.get(simulation.items["processing-unit"]),
        "processing-unit",
    )

    print_result(
        upcycler_results_cache.get(simulation.items["electromagnetic-plant"]),
        "electromagnetic-plant",
    )


def print_result(results: tuple[UpcyclerResult, ...], target: str) -> None:
    print(target)
    for n, result in enumerate(results):
        if n > 0:
            print()

        print(f"BEST PER INPUT: {result.system.upcycler.recycled_item.name}")
        print("\tPer Input:")
        print(
            f"\tInputs: {[{material.name: (quality.name, amount) for material, qualities in result.per_input.legendary_per_input.material_inputs.items() for quality, amount in qualities.amounts.items()}]}"
        )
        print(
            f"\tLegendary: {[{material.name: amount for material, amount in result.per_input.legendary_per_input.legendary_output.items()}]}"
        )
        if result.per_input.legendary_per_input.fluid_outputs:
            print(
                f"\tFluid Output : {[{material.name: (quality.name, amount) for material, qualities in result.per_input.legendary_per_input.fluid_outputs.items() for quality, amount in qualities.amounts.items()}]}"
            )
        print("\tPer Second:")
        print(
            f"\tInputs: {[{material.name: (quality.name, amount) for material, qualities in result.per_input.legendary_per_second.material_inputs.items() for quality, amount in qualities.amounts.items()}]}"
        )
        print(
            f"\tLegendary: {[{material.name: amount for material, amount in result.per_input.legendary_per_second.legendary_output.items()}]}"
        )
        if result.per_input.legendary_per_second.fluid_outputs:
            print(
                f"\tFluid Output : {[{material.name: (quality.name, amount) for material, qualities in result.per_input.legendary_per_second.fluid_outputs.items() for quality, amount in qualities.amounts.items()}]}"
            )
        print(f"BEST PER SECOND: {result.system.upcycler.recycled_item.name}")
        print("\tPer Input:")
        print(
            f"\tInputs: {[{material.name: (quality.name, amount) for material, qualities in result.per_second.legendary_per_input.material_inputs.items() for quality, amount in qualities.amounts.items()}]}"
        )
        print(
            f"\tLegendary: {[{material.name: amount for material, amount in result.per_second.legendary_per_input.legendary_output.items()}]}"
        )
        if result.per_second.legendary_per_input.fluid_outputs:
            print(
                f"\tFluid Output : {[{material.name: (quality.name, amount) for material, qualities in result.per_second.legendary_per_input.fluid_outputs.items() for quality, amount in qualities.amounts.items()}]}"
            )
        print("\tPer Second:")
        print(
            f"\tInputs: {[{material.name: (quality.name, amount) for material, qualities in result.per_second.legendary_per_second.material_inputs.items() for quality, amount in qualities.amounts.items()}]}"
        )
        print(
            f"\tLegendary: {[{material.name: amount for material, amount in result.per_second.legendary_per_second.legendary_output.items()}]}"
        )
        if result.per_second.legendary_per_second.fluid_outputs:
            print(
                f"\tFluid Output : {[{material.name: (quality.name, amount) for material, qualities in result.per_second.legendary_per_second.fluid_outputs.items() for quality, amount in qualities.amounts.items()}]}"
            )

    print()
