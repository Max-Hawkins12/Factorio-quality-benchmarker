from dataclasses import dataclass

from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    Miner,
    Module,
    ModuleEffect,
    Recipe,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified


@dataclass(frozen=True, slots=True)
class ModuledCrafter:
    crafter: Qualified[Crafter]
    modules: tuple[Qualified[Module], ...]


@dataclass(frozen=True, slots=True)
class ModuledBeacon:
    beacon: Qualified[Beacon]
    modules: tuple[Qualified[Module], ...]


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
    modules: set[Qualified[Module]],
) -> frozenset[Qualified[Module]]:
    """
    Return all qualified modules valid for the given machine and recipe.
    """
    allowed_effects = _get_allowed_module_effects(machine, recipe)

    return frozenset(
        module
        for module in modules
        if _is_module_allowed(module.entity, allowed_effects)
    )
