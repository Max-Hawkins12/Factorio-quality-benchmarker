from itertools import combinations_with_replacement, product

from factorio_quality_benchmarker.game.engine import (
    MachineEffects,
    get_allowed_modules,
    get_beacon_effects,
    get_machine_effects,
    get_module_effects,
)
from factorio_quality_benchmarker.game.models import Beacon, Module, ModuleEffect
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine

from .constants import ALL_RECIPE_EFFECTS, NO_EFFECTS, QUALITY
from .models import (
    AllowedRecipeEffects,
    BeaconConfiguration,
    BeaconConfigurationKey,
    MachineConfiguration,
    MachineConfigurationIndex,
    ModuleConfiguration,
    ModuleConfigurationIndex,
)
from .pareto import get_pareto_frontier, get_unique_pareto_frontier


def _get_recipe_modules(
    modules: tuple[Qualified[Module], ...],
    allowed_recipe_effects: AllowedRecipeEffects,
    module_effects: dict[str, ModuleEffect],
) -> tuple[Qualified[Module], ...]:
    """Get the modules allowed by a recipe under the specific allowed effects"""
    productivity = module_effects["productivity"]
    quality = module_effects["quality"]

    return tuple(
        module
        for module in modules
        if (
            productivity not in module.entity.effects
            or allowed_recipe_effects.productivity
        )
        and (
            quality not in module.entity.effects
            or allowed_recipe_effects.quality
            or module.entity.effects[quality] < 0
        )
    )


# Module configurations
def _generate_module_configurations(
    modules: tuple[Qualified[Module], ...],
    num_module_slots: int,
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> tuple[ModuleConfiguration, ...]:
    return tuple(
        ModuleConfiguration(
            modules=configuration,
            effects=get_module_effects(configuration, module_effects, is_2_1),
        )
        for configuration in combinations_with_replacement(
            modules,
            num_module_slots,
        )
    )


def _generate_module_configuration_index(
    modules: tuple[Qualified[Module], ...],
    num_module_slots: int,
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> ModuleConfigurationIndex:
    """Get a dict of Pareto frontier module configurations at every variation of allowed recipe effects."""
    return {
        allowed_recipe_effects: get_unique_pareto_frontier(
            _generate_module_configurations(
                modules=_get_recipe_modules(
                    modules, allowed_recipe_effects, module_effects
                ),
                num_module_slots=num_module_slots,
                module_effects=module_effects,
                is_2_1=is_2_1,
            ),
            allowed_recipe_effects,
        )
        for allowed_recipe_effects in ALL_RECIPE_EFFECTS
    }


# Beacon Configurations
def _generate_beacon_configurations(
    beacon: Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    max_beacons: int,
    module_effects: dict[str, ModuleEffect],
    machine_allowed_effects: frozenset[ModuleEffect],
    is_2_1: bool,
) -> tuple[BeaconConfiguration, ...]:
    """
    Get a tuple of Pareto frontier beaon configurations.

    Beacons only accept speed modules, so their configurations are independent of recipe productivity/quality permissions.
    Quality is still included in the Pareto frontier when the machine supports it because speed modules can reduce quality.
    """
    return get_unique_pareto_frontier(
        tuple(
            BeaconConfiguration(
                num_beacons=num_beacons,
                modules=configuration,
                effects=get_beacon_effects(
                    beacon, configuration, num_beacons, module_effects, is_2_1
                ),
            )
            for num_beacons in range(max_beacons + 1)
            for configuration in combinations_with_replacement(
                modules,
                num_beacons * beacon.entity.module_slots,
            )
        ),
        allowed_recipe_effects=QUALITY
        if module_effects["quality"] in machine_allowed_effects
        else NO_EFFECTS,
    )


# Machine Configurations
def _generate_machine_configuration_index(
    module_configuration_index: ModuleConfigurationIndex,
    beacon_configurations: tuple[BeaconConfiguration, ...],
) -> MachineConfigurationIndex:

    unique_index: dict[
        AllowedRecipeEffects, dict[MachineEffects, MachineConfiguration]
    ] = {}

    for allowed_recipe_effects in module_configuration_index:
        unique: dict[MachineEffects, MachineConfiguration] = {}

        for modules, beacons in product(
            module_configuration_index[allowed_recipe_effects],
            beacon_configurations,
        ):
            effects = get_machine_effects(modules.effects, beacons.effects)

            unique.setdefault(
                effects,
                MachineConfiguration(
                    modules=modules,
                    beacons=beacons,
                    effects=effects,
                ),
            )

        unique_index[allowed_recipe_effects] = unique

    return {
        allowed_recipe_effects: tuple(
            configuration
            for configuration in get_pareto_frontier(
                tuple(unique_index[allowed_recipe_effects].values()),
                allowed_recipe_effects,
            )
        )
        for allowed_recipe_effects in module_configuration_index
    }


# Public API
def generate_machine_configuration_index_for_machine(
    machine: QualifiedMachine,
    modules: tuple[Qualified[Module], ...],
    beacon_configurations: tuple[BeaconConfiguration, ...],
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> MachineConfigurationIndex:

    return _generate_machine_configuration_index(
        module_configuration_index=_generate_module_configuration_index(
            modules=get_allowed_modules(machine, modules, module_effects["quality"]),
            num_module_slots=machine.entity.module_slots,
            module_effects=module_effects,
            is_2_1=is_2_1,
        ),
        beacon_configurations=beacon_configurations,
    )


def generate_beacon_configurations_for_key(
    key: BeaconConfigurationKey,
    beacon: Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> tuple[BeaconConfiguration, ...]:

    return _generate_beacon_configurations(
        beacon=beacon,
        modules=get_allowed_modules(beacon, modules, module_effects["quality"]),
        max_beacons=key.max_beacons,
        module_effects=module_effects,
        machine_allowed_effects=key.allowed_effects,
        is_2_1=is_2_1,
    )
