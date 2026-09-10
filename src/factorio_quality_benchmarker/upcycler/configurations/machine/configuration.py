from itertools import combinations_with_replacement, product

from factorio_quality_benchmarker.game.engine import (
    calculate_maximum_beacons,
    get_allowed_modules,
)
from factorio_quality_benchmarker.game.models import (
    Beacon,
    Module,
    ModuleEffect,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine

from .constants import ALL_RECIPE_EFFECTS, NO_EFFECTS, QUALITY
from .effects import (
    get_beacon_configuration_effects,
    get_machine_configuration_effects,
    get_module_configuration_effects,
)
from .models import (
    BeaconConfiguration,
    EffeciveModuleConfigurationIndex,
    EffectiveBeaconConfiguration,
    EffectiveMachineConfiguration,
    EffectiveModuleConfiguration,
    MachineConfiguration,
    MachineConfigurationIndex,
    MachineEffects,
    ModuleConfiguration,
    ModuleConfigurationIndex,
    RecipeEffects,
)
from .modules import get_desired_modules
from .pareto import get_pareto_frontier, get_unique_pareto_frontier


def _get_recipe_modules(
    modules: tuple[Qualified[Module], ...],
    recipe_effects: RecipeEffects,
    module_effects: dict[str, ModuleEffect],
) -> tuple[Qualified[Module], ...]:
    productivity = module_effects["productivity"]
    quality = module_effects["quality"]

    return tuple(
        module
        for module in modules
        if (productivity not in module.entity.effects or recipe_effects.productivity)
        and (
            quality not in module.entity.effects
            or recipe_effects.quality
            or module.entity.effects[quality] < 0
        )
    )


# Module configurations
def _get_module_configurations(
    modules: tuple[Qualified[Module], ...],
    num_module_slots: int,
) -> tuple[ModuleConfiguration, ...]:
    return tuple(
        ModuleConfiguration(modules=configuration)
        for configuration in combinations_with_replacement(
            modules,
            num_module_slots,
        )
    )


def _get_module_configuration_index(
    modules: tuple[Qualified[Module], ...],
    num_module_slots: int,
    module_effects: dict[str, ModuleEffect],
) -> ModuleConfigurationIndex:
    return {
        recipe_effects: _get_module_configurations(
            _get_recipe_modules(modules, recipe_effects, module_effects),
            num_module_slots,
        )
        for recipe_effects in ALL_RECIPE_EFFECTS
    }


def _get_effective_module_configuration_index(
    machine: QualifiedMachine,
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
) -> EffeciveModuleConfigurationIndex:

    module_config_index = _get_module_configuration_index(
        get_allowed_modules(machine, modules, module_effects["quality"]),
        machine.entity.module_slots,
        module_effects,
    )

    return {
        recipe_effects: get_unique_pareto_frontier(
            tuple(
                EffectiveModuleConfiguration(
                    configuration=configuration,
                    effects=get_module_configuration_effects(
                        configuration,
                        module_effects,
                    ),
                )
                for configuration in module_config_index[recipe_effects]
            ),
            recipe_effects,
        )
        for recipe_effects in module_config_index
    }


# Beacon Configurations
# Beacons only accept speed modules, so we do not need to index them allowing productivity and quality
def _get_beacon_configurations(
    modules: tuple[Qualified[Module], ...],
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


def _get_effective_beacon_configurations(
    beacon: Qualified[Beacon],
    max_beacons: int,
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    machine_allowed_effects: frozenset[ModuleEffect],
) -> tuple[EffectiveBeaconConfiguration, ...]:

    beacon_configs = _get_beacon_configurations(
        modules=tuple(
            module
            for module in get_allowed_modules(
                beacon, modules, module_effects["quality"]
            )
            if all(
                effect in set(machine_allowed_effects | {module_effects["quality"]})
                for effect in module.entity.effects
            )
        ),
        module_slots_per_beacon=beacon.entity.module_slots,
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
        ),
        recipe_effects=QUALITY
        if module_effects["quality"] in machine_allowed_effects
        else NO_EFFECTS,
    )


# Machine Configurations
def _get_machine_configuration_index(
    module_configuration_index: EffeciveModuleConfigurationIndex,
    beacon_configurations: tuple[EffectiveBeaconConfiguration, ...],
) -> MachineConfigurationIndex:

    unique_index: dict[
        RecipeEffects, dict[MachineEffects, EffectiveMachineConfiguration]
    ] = {}

    for recipe_effects in module_configuration_index:
        unique: dict[MachineEffects, EffectiveMachineConfiguration] = {}

        for modules, beacons in product(
            module_configuration_index[recipe_effects],
            beacon_configurations,
        ):
            effects = get_machine_configuration_effects(
                modules.effects, beacons.effects
            )

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

        unique_index[recipe_effects] = unique

    return {
        recipe_effects: tuple(
            configuration.configuration
            for configuration in get_pareto_frontier(
                tuple(unique_index[recipe_effects].values()),
                recipe_effects,
            )
        )
        for recipe_effects in module_configuration_index
    }


# Cashing for beacon layouts of a given max size
def _get_beacon_configurations_for_max(
    machine: QualifiedMachine,
    beacon: Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    beacon_configurations_by_max_and_effects: dict[
        tuple[int, frozenset[ModuleEffect]], tuple[EffectiveBeaconConfiguration, ...]
    ],
) -> tuple[EffectiveBeaconConfiguration, ...]:
    max_beacons = calculate_maximum_beacons(machine.entity, beacon.entity)
    allowed_effects = machine.entity.allowed_effects

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
    machines: dict[str, QualifiedMachine],
    beacons: dict[str, Qualified[Beacon]],
    all_modules: dict[str, Qualified[Module]],
    module_effects: dict[str, ModuleEffect],
) -> dict[QualifiedMachine, MachineConfigurationIndex]:
    beacon = beacons["beacon"]
    modules: tuple[Qualified[Module], ...] = get_desired_modules(
        tuple(all_modules.values()),
        module_effects,
    )

    beacon_configurations_by_max_and_effects: dict[
        tuple[int, frozenset[ModuleEffect]], tuple[EffectiveBeaconConfiguration, ...]
    ] = {}

    return {
        machine: _get_machine_configuration_index(
            module_configuration_index=_get_effective_module_configuration_index(
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
