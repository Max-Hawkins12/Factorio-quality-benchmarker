import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.game.engine import (
    get_frontier_desired_modules,
)
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    ALL_RECIPE_EFFECTS,
    BeaconConfiguration,
    BeaconConfigurationKey,
    MachineConfigurationIndex,
)
from factorio_quality_benchmarker.upcycler.configurations.recipe import (
    generate_recipe_configurations_for_recipe,
)
from factorio_quality_benchmarker.upcycler.graphs import get_machine_configuration_index
from factorio_quality_benchmarker.upcycler.simulation import (
    NO_RESEARCH,
    QualifiedMachine,
    RunConfig,
    UpcyclerScope,
    build_simulation_context,
)

app = typer.Typer()


@app.command()
def parse() -> None:
    perform_parsing()


@app.command()
def dev() -> None:
    # Temp command

    game_data = load_game_data()

    simulation = build_simulation_context(
        game_data,
        RunConfig(
            productivity_levels=NO_RESEARCH,
            upcycler_scope=UpcyclerScope.CURATED,
            entity_quality=game_data.qualities["legendary"],
            desired_quality=game_data.qualities["legendary"],
        ),
    )

    beacon_configuration_cache: dict[
        BeaconConfigurationKey, tuple[BeaconConfiguration, ...]
    ] = {}
    machine_configuration_cache: dict[QualifiedMachine, MachineConfigurationIndex] = {}

    effects = dict(simulation.game_data.module_effects)

    modules = get_frontier_desired_modules(
        tuple(simulation.modules.values()),
        effects,
        simulation.game_data.is_2_1,
    )

    beacon = simulation.beacon

    for machine in simulation.machines.values():
        config_index = get_machine_configuration_index(
            machine,
            beacon,
            modules,
            effects,
            beacon_configuration_cache,
            machine_configuration_cache,
            simulation.game_data.is_2_1,
        )

        print(f"{machine.name}")
        for e in ALL_RECIPE_EFFECTS:
            print(
                f"\tProductivity: {e.productivity} Quality: {e.quality} number of configs: {len(config_index[e])}"
            )

    testing_recipe = simulation.recipes["iron-plate"]

    print(testing_recipe.name)
    testing_recipe_configs = generate_recipe_configurations_for_recipe(
        testing_recipe,
        dict(simulation.qualities),
        dict(simulation.crafters),
        machine_configuration_cache,
        dict(simulation.productivity_research_index),
    )

    print(
        f"Recipe configurations: Normal: {len(testing_recipe_configs[simulation.qualities['normal']])} Legendary: {len(testing_recipe_configs[simulation.qualities['legendary']])}"
    )
