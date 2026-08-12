"""
beacon: "distribution_effectivity_bonus_per_quality_level": 0.2,

normal scaling = speed * 1 + (0.3 *q_level)

2.0
module scaling = effect * floor(1 + (0.3 *q_level))

2.1
module scaling = effect * (1 + (0.3 *q_level))


beacon scaling = distribution + 0.2 * q_level

"""

from collections.abc import Mapping
from math import floor

from factorio_quality_benchmarker.model import (
    ModuleEffect,
    QualifiedBeacon,
    QualifiedCrafter,
    QualifiedModule,
)

DEFAULT_QUALITY_SCALE = 0.3


QUALITY_MODULE_SCALED_EFFECT = {
    "speed": "speed",
    "efficiency": "consumption",
    "productivity": "productivity",
    "quality": "quality",
}


def apply_crafter_quality_speed(crafter: QualifiedCrafter) -> float:
    """
    Apply the Factorio engine calculation to determine a crafter's speed at a quality level
    """

    crafting_speed = crafter.crafter.crafting_speed
    quality_level = crafter.quality.level

    return crafting_speed * (1 + DEFAULT_QUALITY_SCALE * quality_level)


def apply_module_quality(
    module: QualifiedModule, is_2_1: bool
) -> Mapping[ModuleEffect, float]:
    """
    Apply the Factorio engine calculation to determine a modules's effects at a quality level
    """
    scaled_effect_name = QUALITY_MODULE_SCALED_EFFECT[module.module.category.type]

    scaled_effect = next(
        effect
        for effect in module.module.effects
        if effect.effect == scaled_effect_name
    )
    base_value = module.module.effects[scaled_effect]

    qualified_value = base_value * (1 + 0.3 * module.quality.level)

    resolution = 0.0001 if is_2_1 else 0.001
    qualified_value = floor(qualified_value / resolution) * resolution

    return {
        effect: qualified_value if effect == scaled_effect else value
        for effect, value in module.module.effects.items()
    }


def apply_beacon_quality_distribution_effectivity(beacon: QualifiedBeacon) -> float:
    """
    Apply the Factorio engine calculation to determine a beacons's distribution effectivity at a quality level
    """
    bonus_per_quality_level = (
        beacon.beacon.distribution_effectivity_bonus_per_quality_level
    )
    distribution_effectivity = beacon.beacon.distribution_effectivity
    quality_level = beacon.quality.level

    return distribution_effectivity + bonus_per_quality_level * quality_level
