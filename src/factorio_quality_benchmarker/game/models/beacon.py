from dataclasses import dataclass

from .common import ModuleEffect


@dataclass(frozen=True, slots=True)
class Beacon:
    name: str

    distribution_effectivity: float
    distribution_effectivity_bonus_per_quality_level: float
    diminishing_returns_profile: tuple[float, ...]

    effect_range: int

    module_slots: int
    allowed_effects: frozenset[ModuleEffect]
    width: int
    height: int
