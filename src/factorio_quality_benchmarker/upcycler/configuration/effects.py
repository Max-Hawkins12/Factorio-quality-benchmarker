from factorio_quality_benchmarker.game.engine import calculate_distribution_effectivity
from factorio_quality_benchmarker.game.models import Beacon, ModuleEffect
from factorio_quality_benchmarker.upcycler.simulation import Qualified

from .models import (
    BeaconConfiguration,
    MachineEffects,
    ModuleConfiguration,
)


def get_module_configuration_effects(
    configuration: ModuleConfiguration,
    effects: dict[str, ModuleEffect],
) -> MachineEffects:
    return MachineEffects(
        speed=round(
            sum(
                module.entity.effects.get(effects["speed"], 0.0)
                for module in configuration.modules
            ),
            10,
        ),
        productivity=round(
            sum(
                module.entity.effects.get(effects["productivity"], 0.0)
                for module in configuration.modules
            ),
            10,
        ),
        quality=round(
            sum(
                module.entity.effects.get(effects["quality"], 0.0)
                for module in configuration.modules
            ),
            10,
        ),
    )


def get_beacon_configuration_effects(
    configuration: BeaconConfiguration,
    effects: dict[str, ModuleEffect],
    beacon: Qualified[Beacon],
) -> MachineEffects:

    module_effects = get_module_configuration_effects(configuration.modules, effects)

    effectivity = calculate_distribution_effectivity(beacon, configuration.num_beacons)

    return MachineEffects(
        speed=round(module_effects.speed * effectivity, 10),
        productivity=round(module_effects.productivity * effectivity, 10),
        quality=round(module_effects.quality * effectivity, 10),
    )


def get_machine_configuration_effects(
    module_effects: MachineEffects,
    beacon_effects: MachineEffects,
) -> MachineEffects:
    return MachineEffects(
        speed=round(module_effects.speed + beacon_effects.speed, 10),
        productivity=round(
            module_effects.productivity + beacon_effects.productivity, 10
        ),
        quality=round(module_effects.quality + beacon_effects.quality, 10),
    )
