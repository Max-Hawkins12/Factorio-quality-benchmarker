from factorio_quality_benchmarker.game.models import Module, ModuleEffect
from factorio_quality_benchmarker.upcycler.simulation import EMPTY_MODULE, Qualified

from .constants import DESIRED_MODULE_EFFECTS


def _get_desired_module_effects(
    effects: dict[str, ModuleEffect],
) -> tuple[ModuleEffect, ...]:
    return tuple(effects[effect] for effect in DESIRED_MODULE_EFFECTS)


def _module_dominates(
    a: Module,
    b: Module,
    effects: tuple[ModuleEffect, ...],
) -> bool:

    a_effects = tuple(a.effects.get(effect, 0.0) for effect in effects)
    b_effects = tuple(b.effects.get(effect, 0.0) for effect in effects)

    return all(a >= b for a, b in zip(a_effects, b_effects)) and any(
        a > b for a, b in zip(a_effects, b_effects)
    )


def get_desired_modules(
    modules: tuple[Qualified[Module], ...],
    effects: dict[str, ModuleEffect],
) -> tuple[Qualified[Module], ...]:

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
            _module_dominates(other.entity, module.entity, desired_effects)
            for other in relevant_modules
            if other is not module
        )
    ) + (EMPTY_MODULE,)
