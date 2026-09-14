from collections.abc import Callable

from factorio_quality_benchmarker.game.engine import calculate_maximum_beacons
from factorio_quality_benchmarker.game.models import Beacon, Module, ModuleEffect
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    BeaconConfiguration,
    BeaconConfigurationKey,
    MachineConfigurationIndex,
    generate_beacon_configurations_for_key,
    generate_machine_configuration_index_for_machine,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine


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
    is_2_1: bool,
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
                    is_2_1=is_2_1,
                ),
            ),
            module_effects=module_effects,
            is_2_1=is_2_1,
        ),
    )
