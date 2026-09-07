from itertools import combinations_with_replacement, product

from factorio_quality_benchmarker.game.models import Module

from .models import BeaconConfiguration, MachineConfiguration, ModuleConfiguration


def get_module_configurations(
    modules: tuple[Module, ...],
    num_module_slots: int,
) -> tuple[ModuleConfiguration, ...]:
    return tuple(
        ModuleConfiguration(modules=configuration)
        for configuration in combinations_with_replacement(
            modules,
            num_module_slots,
        )
    )


def get_beacon_configurations(
    module_configurations: tuple[ModuleConfiguration, ...],
    max_beacons: int,
) -> tuple[BeaconConfiguration, ...]:
    return tuple(
        BeaconConfiguration(beacons=configuration)
        for num_beacons in range(max_beacons + 1)
        for configuration in combinations_with_replacement(
            module_configurations,
            num_beacons,
        )
    )


def get_machine_configurations(
    module_configurations: tuple[ModuleConfiguration, ...],
    beacon_configurations: tuple[BeaconConfiguration, ...],
) -> tuple[MachineConfiguration, ...]:
    return tuple(
        MachineConfiguration(
            modules=modules,
            beacons=beacons,
        )
        for modules, beacons in product(
            module_configurations,
            beacon_configurations,
        )
    )
