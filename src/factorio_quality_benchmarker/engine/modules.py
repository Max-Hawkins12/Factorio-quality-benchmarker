from dataclasses import dataclass
from itertools import combinations_with_replacement

from factorio_quality_benchmarker.model import (
    Beacon,
    Crafter,
    Miner,
    Module,
    ModuleEffect,
    QualifiedBeacon,
    QualifiedCrafter,
    QualifiedMiner,
    QualifiedModule,
    Recipe,
)

from .beacons import calculate_maximum_number_of_beacons


@dataclass(frozen=True, slots=True)
class ModuledCrafter:
    crafter: QualifiedCrafter
    modules: tuple[QualifiedModule, ...]


@dataclass(frozen=True, slots=True)
class ModuledBeacon:
    beacon: QualifiedBeacon
    modules: tuple[QualifiedModule, ...]


@dataclass(frozen=True, slots=True)
class BeaconedCrafter:
    crafter: ModuledCrafter
    beacons: tuple[ModuledBeacon, ...]


def _get_allowed_module_effects(
    machine: Beacon | Crafter | Miner,
    recipe: Recipe,
) -> frozenset[ModuleEffect]:
    """
    Return the module effects allowed for the given machine and recipe.
    """
    allowed_effects = set(machine.allowed_effects)

    if not recipe.allow_productivity:
        allowed_effects.discard("productivity")

    if not recipe.allow_quality:
        allowed_effects.discard("quality")

    return frozenset(allowed_effects)


def _is_module_allowed(
    module: Module,
    allowed_effects: frozenset[ModuleEffect],
) -> bool:
    """
    Return whether all effects of the module are allowed.
    """
    return module.effects.keys() <= allowed_effects


def _get_allowed_modules(
    machine: Beacon | Crafter | Miner,
    recipe: Recipe,
    modules: set[QualifiedModule],
) -> frozenset[QualifiedModule]:
    """
    Return all qualified modules valid for the given machine and recipe.
    """
    allowed_effects = _get_allowed_module_effects(machine, recipe)

    return frozenset(
        module
        for module in modules
        if _is_module_allowed(module.module, allowed_effects)
    )


def _generate_module_configurations(
    allowed_modules: frozenset[QualifiedModule],
    module_slots: int,
) -> frozenset[tuple[QualifiedModule, ...]]:
    """
    Generate every module configuration using up to the given number of slots.

    Slot ordering is irrelevant, but duplicate modules are allowed.
    """
    configurations: set[tuple[QualifiedModule, ...]] = {()}

    for slots_used in range(1, module_slots + 1):
        configurations.update(
            combinations_with_replacement(
                allowed_modules,
                slots_used,
            )
        )

    return frozenset(configurations)


def _generate_beacon_configurations(
    available_beacons: frozenset[ModuledBeacon],
    maximum_beacons: int,
) -> frozenset[tuple[ModuledBeacon, ...]]:
    """
    Generate every beacon configuration using up to the maximum number
    of beacons.

    Beacon ordering is irrelevant, but duplicate beacon configurations
    are allowed.
    """
    configurations: set[tuple[ModuledBeacon, ...]] = {()}

    for beacon_count in range(1, maximum_beacons + 1):
        configurations.update(
            combinations_with_replacement(
                available_beacons,
                beacon_count,
            )
        )

    return frozenset(configurations)


def get_full_module_beacon_arrangements(
    crafter: QualifiedCrafter,
    recipe: Recipe,
    beacon: QualifiedBeacon,
    modules: set[QualifiedModule],
) -> frozenset[BeaconedCrafter]:
    """
    Generate every valid combination of machine modules and beacon
    configurations for the given crafter and recipe.
    """
    crafter_allowed_modules = _get_allowed_modules(
        crafter.machine,
        recipe,
        modules,
    )

    beacon_allowed_modules = _get_allowed_modules(
        beacon.beacon,
        recipe,
        modules,
    )

    crafter_module_configurations = _generate_module_configurations(
        crafter_allowed_modules,
        crafter.machine.module_slots,
    )

    beacon_module_configurations = _generate_module_configurations(
        beacon_allowed_modules,
        beacon.beacon.module_slots,
    )

    available_beacons = frozenset(
        ModuledBeacon(
            beacon=beacon,
            modules=module_configuration,
        )
        for module_configuration in beacon_module_configurations
    )

    maximum_beacons = calculate_maximum_number_of_beacons(
        crafter.machine,
        beacon.beacon,
    )

    beacon_configurations = _generate_beacon_configurations(
        available_beacons,
        maximum_beacons,
    )

    return frozenset(
        BeaconedCrafter(
            crafter=ModuledCrafter(
                crafter=crafter,
                modules=crafter_modules,
            ),
            beacons=beacons,
        )
        for crafter_modules in crafter_module_configurations
        for beacons in beacon_configurations
    )
