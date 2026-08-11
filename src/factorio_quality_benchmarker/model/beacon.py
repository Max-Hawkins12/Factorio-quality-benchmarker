from dataclasses import dataclass

from .common import ModuleCategory, ModuleEffect


@dataclass(frozen=True, slots=True)
class Beacon:
    name: str

    distribution_effectivity: float
    distribution_effectivity_bonus_per_quality_level: float

    diminishing_returns_profile: tuple[int, ...]

    module_slots: int

    allowed_effects: frozenset[ModuleEffect]
    allowed_module_categories: frozenset[ModuleCategory]

    effect_area_distance: int
