from collections.abc import Callable

import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.game.engine import (
    calculate_maximum_beacons,
    get_frontier_desired_modules,
)
from factorio_quality_benchmarker.game.models import Beacon, Module, ModuleEffect
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    ALL_RECIPE_EFFECTS,
    BeaconConfiguration,
    BeaconConfigurationKey,
    MachineConfigurationIndex,
    generate_beacon_configurations_for_key,
    generate_machine_configuration_index_for_machine,
)
from factorio_quality_benchmarker.upcycler.simulation import (
    NO_RESEARCH,
    Qualified,
    QualifiedMachine,
    RunConfig,
    UpcyclerScope,
    build_simulation_context,
)

app = typer.Typer()


@app.command()
def parse() -> None:
    perform_parsing()


# TEMP TO MOVE LATER
def get_from_cache[K, V](
    cache: dict[K, V],
    key: K,
    calculate: Callable[[], V],
) -> V:
    if key not in cache:
        cache[key] = calculate()

    return cache[key]


def get_machine_configuration_index(
    machine: QualifiedMachine,
    beacon: Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    beacon_configuration_cache: dict[
        BeaconConfigurationKey, tuple[BeaconConfiguration, ...]
    ],
    machine_configuration_cache: dict[QualifiedMachine, MachineConfigurationIndex],
) -> MachineConfigurationIndex:

    beacon_key = BeaconConfigurationKey(
        allowed_effects=machine.entity.allowed_effects,
        max_beacons=calculate_maximum_beacons(machine.entity, beacon.entity),
    )

    return get_from_cache(
        cache=machine_configuration_cache,
        key=machine,
        calculate=lambda: generate_machine_configuration_index_for_machine(
            machine=machine,
            modules=modules,
            beacon_configurations=get_from_cache(
                cache=beacon_configuration_cache,
                key=beacon_key,
                calculate=lambda: generate_beacon_configurations_for_key(
                    key=beacon_key,
                    beacon=beacon,
                    modules=modules,
                    module_effects=module_effects,
                ),
            ),
            module_effects=module_effects,
        ),
    )


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
        )

        print(f"{machine.name}")
        for e in ALL_RECIPE_EFFECTS:
            print(
                f"\tProductivity: {e.productivity} Quality: {e.quality} number of configs: {len(config_index[e])}"
            )
