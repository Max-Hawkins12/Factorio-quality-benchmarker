from math import floor

from factorio_quality_benchmarker.game.models import (
    Beacon,
    Crafter,
    Module,
    ModuleEffect,
    Quality,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified

DEFAULT_QUALITY_SCALE = 0.3


QUALITY_MODULE_SCALED_EFFECT = {
    "speed": "speed",
    "efficiency": "consumption",
    "productivity": "productivity",
    "quality": "quality",
}


def _quality_multiplier(
    quality: Quality,
    scale: float = DEFAULT_QUALITY_SCALE,
) -> float:
    return 1 + scale * quality.level


def get_qualified_crafting_speed(
    crafter: Qualified[Crafter],
) -> float:
    return crafter.entity.crafting_speed * _quality_multiplier(crafter.quality)


def get_qualified_module_effects(
    module: Qualified[Module],
    is_2_1: bool,
) -> dict[ModuleEffect, float]:
    scaled_effect_name = QUALITY_MODULE_SCALED_EFFECT[module.entity.category.type]

    scaled_effect = next(
        effect
        for effect in module.entity.effects
        if effect.effect == scaled_effect_name
    )

    resolution = 0.0001 if is_2_1 else 0.001

    qualified_value = (
        floor(
            module.entity.effects[scaled_effect]
            * _quality_multiplier(module.quality)
            / resolution
        )
        * resolution
    )

    return {
        effect: (qualified_value if effect == scaled_effect else value)
        for effect, value in module.entity.effects.items()
    }


def get_qualified_beacon_distribution_effectivity(
    beacon: Qualified[Beacon],
) -> float:
    return (
        beacon.entity.distribution_effectivity
        + beacon.entity.distribution_effectivity_bonus_per_quality_level
        * beacon.quality.level
    )
