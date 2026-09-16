from factorio_quality_benchmarker.game.models import (
    Beacon,
    Module,
    ModuleEffect,
)
from factorio_quality_benchmarker.optimiser.simulation import (
    EMPTY_MODULE,
    Qualified,
    QualifiedMachine,
)

from .constants import DESIRED_MODULE_EFFECTS
from .quality import get_qualified_module_effects


def get_allowed_modules(
    machine: QualifiedMachine | Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    quality_effect: ModuleEffect,
) -> tuple[Qualified[Module], ...]:
    """
    Get only the machines which are allowed by this machine
    """
    return tuple(
        module
        for module in modules
        if all(
            effect in machine.entity.allowed_effects
            or (
                effect == quality_effect and value < 0
            )  # Even if the machine disallows quality, a negative quality on a module is permitted by the engine
            for effect, value in module.entity.effects.items()
        )
    )


def _get_desired_module_effects(
    effects: dict[str, ModuleEffect],
) -> tuple[ModuleEffect, ...]:
    return tuple(effects[effect] for effect in DESIRED_MODULE_EFFECTS)


def _module_dominates(
    a: Qualified[Module],
    b: Qualified[Module],
    effects: tuple[ModuleEffect, ...],
    is_2_1: bool,
) -> bool:

    a_effects = tuple(
        get_qualified_module_effects(a, is_2_1).get(effect, 0.0) for effect in effects
    )
    b_effects = tuple(
        get_qualified_module_effects(b, is_2_1).get(effect, 0.0) for effect in effects
    )

    return all(a >= b for a, b in zip(a_effects, b_effects)) and any(
        a > b for a, b in zip(a_effects, b_effects)
    )


def get_frontier_desired_modules(
    modules: tuple[Qualified[Module], ...],
    effects: dict[str, ModuleEffect],
    is_2_1: bool,
) -> tuple[Qualified[Module], ...]:
    """
    Get only the modules which have at least one desired effect, and which are Pareto dominant.

    Also include a placeholder EMPTY_MODULE to simulte an empty slot.
    """

    desired_effects = _get_desired_module_effects(effects)

    relevant_modules = tuple(
        module
        for module in modules
        if any(effect in module.entity.effects for effect in desired_effects)
    )

    return tuple(
        module
        for module in relevant_modules
        if not any(
            _module_dominates(other, module, desired_effects, is_2_1)
            for other in relevant_modules
            if other is not module
        )
    ) + (EMPTY_MODULE,)
