from factorio_quality_benchmarker.game.models import (
    Beacon,
    Module,
    ModuleEffect,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine


def get_allowed_modules(
    machine: QualifiedMachine | Qualified[Beacon],
    modules: tuple[Qualified[Module], ...],
    quality_effect: ModuleEffect,
) -> tuple[Qualified[Module], ...]:
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
