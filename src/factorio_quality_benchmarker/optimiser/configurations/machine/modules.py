from collections.abc import Mapping

from factorio_quality_benchmarker.game.engine import get_qualified_module_effects
from factorio_quality_benchmarker.game.models import Module, ModuleEffect
from factorio_quality_benchmarker.optimiser.simulation import EMPTY_MODULE, Qualified

from .constants import DESIRED_MODULE_EFFECTS


def _get_desired_module_effects(
    effects: Mapping[str, ModuleEffect],
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
    effects: Mapping[str, ModuleEffect],
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
