from itertools import combinations_with_replacement, product

from factorio_quality_benchmarker.game.engine import (
    calculate_maximum_beacons,
    get_allowed_modules,
)
from factorio_quality_benchmarker.game.models import (
    Beacon,
    Machine,
    Module,
    ModuleEffect,
)

from .effects import (
    get_beacon_configuration_effects,
    get_machine_configuration_effects,
    get_module_configuration_effects,
)
from .models import (
    BeaconConfiguration,
    EffectiveBeaconConfiguration,
    EffectiveMachineConfiguration,
    EffectiveModuleConfiguration,
    MachineConfiguration,
    MachineEffects,
    ModuleConfiguration,
)
from .modules import get_desired_modules
from .pareto import get_pareto_frontier, get_unique_pareto_frontier


# Configuration helpers
def _get_module_configurations(
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


def _get_beacon_configurations(
    modules: tuple[Module, ...],
    module_slots_per_beacon: int,
    max_beacons: int,
) -> tuple[BeaconConfiguration, ...]:
    return tuple(
        BeaconConfiguration(
            num_beacons=num_beacons,
            modules=ModuleConfiguration(modules=configuration),
        )
        for num_beacons in range(max_beacons + 1)
        for configuration in combinations_with_replacement(
            modules,
            num_beacons * module_slots_per_beacon,
        )
    )


def _get_effective_module_configurations(
    machine: Machine,
    modules: tuple[Module, ...],
    module_effects: dict[str, ModuleEffect],
) -> tuple[EffectiveModuleConfiguration, ...]:

    module_configs = _get_module_configurations(
        modules=get_allowed_modules(machine, modules, module_effects["quality"]),
        num_module_slots=machine.module_slots,
    )

    return get_unique_pareto_frontier(
        tuple(
            EffectiveModuleConfiguration(
                configuration=configuration,
                effects=get_module_configuration_effects(
                    configuration,
                    module_effects,
                ),
            )
            for configuration in module_configs
        )
    )


def _get_effective_beacon_configurations(
    beacon: Beacon,
    max_beacons: int,
    modules: tuple[Module, ...],
    module_effects: dict[str, ModuleEffect],
    machine_allowed_effects: frozenset[ModuleEffect],
) -> tuple[EffectiveBeaconConfiguration, ...]:

    beacon_configs = _get_beacon_configurations(
        modules=tuple(
            module
            for module in get_allowed_modules(
                beacon, modules, module_effects["quality"]
            )
            if all(effect in machine_allowed_effects for effect in module.effects)
        ),
        module_slots_per_beacon=beacon.module_slots,
        max_beacons=max_beacons,
    )

    return get_unique_pareto_frontier(
        tuple(
            EffectiveBeaconConfiguration(
                configuration=configuration,
                effects=get_beacon_configuration_effects(
                    configuration,
                    module_effects,
                    beacon,
                ),
            )
            for configuration in beacon_configs
        )
    )


def _get_machine_configurations(
    module_configurations: tuple[EffectiveModuleConfiguration, ...],
    beacon_configurations: tuple[EffectiveBeaconConfiguration, ...],
) -> tuple[MachineConfiguration, ...]:

    unique: dict[MachineEffects, EffectiveMachineConfiguration] = {}

    for modules, beacons in product(
        module_configurations,
        beacon_configurations,
    ):
        effects = get_machine_configuration_effects(modules.effects, beacons.effects)

        unique.setdefault(
            effects,
            EffectiveMachineConfiguration(
                configuration=MachineConfiguration(
                    modules=modules.configuration,
                    beacons=beacons.configuration,
                ),
                effects=effects,
            ),
        )

    return tuple(
        configuration.configuration
        for configuration in get_pareto_frontier(tuple(unique.values()))
    )


# Cashing for beacon layouts of a given max size
def _get_beacon_configurations_for_max(
    machine: Machine,
    beacon: Beacon,
    modules: tuple[Module, ...],
    module_effects: dict[str, ModuleEffect],
    beacon_configurations_by_max_and_effects: dict[
        tuple[int, frozenset[ModuleEffect]], tuple[EffectiveBeaconConfiguration, ...]
    ],
) -> tuple[EffectiveBeaconConfiguration, ...]:
    max_beacons = calculate_maximum_beacons(machine, beacon)
    allowed_effects = machine.allowed_effects

    if max_beacons not in beacon_configurations_by_max_and_effects:
        beacon_configurations_by_max_and_effects[(max_beacons, allowed_effects)] = (
            _get_effective_beacon_configurations(
                beacon,
                max_beacons,
                modules,
                module_effects,
                allowed_effects,
            )
        )

    return beacon_configurations_by_max_and_effects[(max_beacons, allowed_effects)]


# Public API
def get_best_configurations(
    machines: dict[str, Machine],
    beacons: dict[str, Beacon],
    all_modules: dict[str, Module],
    module_effects: dict[str, ModuleEffect],
) -> dict[Machine, tuple[MachineConfiguration, ...]]:
    beacon = beacons["beacon"]
    modules: tuple[Module, ...] = get_desired_modules(
        tuple(all_modules.values()),
        module_effects,
    )

    beacon_configurations_by_max_and_effects: dict[
        tuple[int, frozenset[ModuleEffect]], tuple[EffectiveBeaconConfiguration, ...]
    ] = {}

    return {
        machine: _get_machine_configurations(
            module_configurations=_get_effective_module_configurations(
                machine,
                modules,
                module_effects,
            ),
            beacon_configurations=_get_beacon_configurations_for_max(
                machine,
                beacon,
                modules,
                module_effects,
                beacon_configurations_by_max_and_effects,
            ),
        )
        for machine in machines.values()
    }
