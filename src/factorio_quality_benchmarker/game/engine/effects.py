from factorio_quality_benchmarker.game.models import Beacon, Module, ModuleEffect
from factorio_quality_benchmarker.upcycler.simulation import Qualified

from .beacons import calculate_distribution_effectivity
from .models import MachineEffects


def get_module_effects(
    modules: tuple[Qualified[Module], ...],
    effects: dict[str, ModuleEffect],
) -> MachineEffects:
    return MachineEffects(
        speed=round(
            sum(module.entity.effects.get(effects["speed"], 0.0) for module in modules),
            10,
        ),
        productivity=round(
            sum(
                module.entity.effects.get(effects["productivity"], 0.0)
                for module in modules
            ),
            10,
        ),
        quality=round(
            sum(
                module.entity.effects.get(effects["quality"], 0.0) for module in modules
            ),
            10,
        ),
    )


def get_beacon_effects(
    modules: tuple[Qualified[Module], ...],
    num_beacons: int,
    effects: dict[str, ModuleEffect],
    beacon: Qualified[Beacon],
) -> MachineEffects:

    module_effects = get_module_effects(modules, effects)

    effectivity = calculate_distribution_effectivity(beacon, num_beacons)

    return MachineEffects(
        speed=round(module_effects.speed * effectivity, 10),
        productivity=round(module_effects.productivity * effectivity, 10),
        quality=round(module_effects.quality * effectivity, 10),
    )


def get_machine_effects(
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
