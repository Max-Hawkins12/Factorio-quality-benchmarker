from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import combinations_with_replacement, product

from factorio_quality_benchmarker.game.engine import (
    MachineEffects,
    get_allowed_modules,
    get_machine_effects,
    get_module_effects,
)
from factorio_quality_benchmarker.game.models import Module, ModuleEffect
from factorio_quality_benchmarker.optimiser.configurations.cache import get_from_cache
from factorio_quality_benchmarker.optimiser.simulation import (
    Qualified,
    QualifiedMachine,
)

from .beacon_configurations import BeaconConfigurationCache
from .constants import ALL_RECIPE_EFFECTS
from .models import (
    AllowedRecipeEffects,
    BeaconConfiguration,
    MachineConfiguration,
    MachineConfigurationIndex,
    ModuleConfiguration,
    ModuleConfigurationIndex,
)
from .modules import get_frontier_desired_modules
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


def _generate_machine_configuration_index_for_machine(
    machine: QualifiedMachine,
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
    beacon_configuration_cache: BeaconConfigurationCache,
) -> MachineConfigurationIndex:

    beacon_configurations = beacon_configuration_cache.get(machine)

    return _generate_machine_configuration_index(
        module_configuration_index=_generate_module_configuration_index(
            modules=get_frontier_desired_modules(
                get_allowed_modules(machine, modules, module_effects["quality"]),
                module_effects,
                is_2_1,
            ),
            num_module_slots=machine.entity.module_slots,
            module_effects=module_effects,
            is_2_1=is_2_1,
        ),
        beacon_configurations=beacon_configurations,
    )


@dataclass(slots=True)
class MachineConfigurationCache:
    modules: tuple[Qualified[Module], ...]
    module_effects: Mapping[str, ModuleEffect]
    is_2_1: bool

    beacon_cache: BeaconConfigurationCache

    _cache: dict[
        QualifiedMachine,
        MachineConfigurationIndex,
    ] = field(default_factory=dict)

    def get(self, machine: QualifiedMachine) -> MachineConfigurationIndex:

        return get_from_cache(
            cache=self._cache,
            key=machine,
            calculate=lambda: _generate_machine_configuration_index_for_machine(
                machine=machine,
                modules=self.modules,
                module_effects=dict(self.module_effects),
                is_2_1=self.is_2_1,
                beacon_configuration_cache=self.beacon_cache,
            ),
        )
