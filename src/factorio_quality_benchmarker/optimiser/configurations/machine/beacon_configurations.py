from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import combinations_with_replacement

from factorio_quality_benchmarker.game.engine import (
    calculate_maximum_beacons,
    get_allowed_modules,
    get_beacon_effects,
)
from factorio_quality_benchmarker.game.models import Beacon, Module, ModuleEffect
from factorio_quality_benchmarker.optimiser.configurations.cache import get_from_cache
from factorio_quality_benchmarker.optimiser.simulation import (
    Qualified,
    QualifiedMachine,
)

from .constants import NO_EFFECTS, QUALITY
from .models import BeaconConfiguration, BeaconConfigurationKey
from .modules import get_frontier_desired_modules
from .pareto import get_unique_pareto_frontier


def _generate_beacon_configurations_for_key(
    key: BeaconConfigurationKey,
    beacon: Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    module_effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> tuple[BeaconConfiguration, ...]:
    """
    Get a tuple of Pareto frontier beacon configurations.

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
            for num_beacons in range(key.max_beacons + 1)
            for configuration in combinations_with_replacement(
                get_frontier_desired_modules(
                    get_allowed_modules(beacon, modules, module_effects["quality"]),
                    module_effects,
                    is_2_1,
                ),
                num_beacons * beacon.entity.module_slots,
            )
        ),
        allowed_recipe_effects=QUALITY
        if module_effects["quality"] in key.allowed_effects
        else NO_EFFECTS,
    )


@dataclass(slots=True)
class BeaconConfigurationCache:
    beacon: Qualified[Beacon]
    modules: tuple[Qualified[Module], ...]
    module_effects: Mapping[str, ModuleEffect]
    is_2_1: bool

    _cache: dict[
        BeaconConfigurationKey,
        tuple[BeaconConfiguration, ...],
    ] = field(default_factory=dict)

    def get(self, machine: QualifiedMachine) -> tuple[BeaconConfiguration, ...]:

        key = BeaconConfigurationKey(
            allowed_effects=machine.entity.allowed_effects,
            max_beacons=calculate_maximum_beacons(machine.entity, self.beacon.entity),
        )

        return get_from_cache(
            cache=self._cache,
            key=key,
            calculate=lambda: _generate_beacon_configurations_for_key(
                key=key,
                beacon=self.beacon,
                modules=self.modules,
                module_effects=dict(self.module_effects),
                is_2_1=self.is_2_1,
            ),
        )
