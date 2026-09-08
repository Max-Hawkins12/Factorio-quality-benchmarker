from factorio_quality_benchmarker.game.models import Module, ModuleEffect, ModuleMachine


def get_allowed_modules(
    machine: ModuleMachine,
    modules: tuple[Module, ...],
    quality_effect: ModuleEffect,
) -> tuple[Module, ...]:
    return tuple(
        module
        for module in modules
        if all(
            effect in machine.allowed_effects
            or (
                effect == quality_effect and value < 0
            )  # Even if the machine disallows quality, a negative quality on a module is permitted by the engine
            for effect, value in module.effects.items()
        )
    )
