from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Beacon:
    name: str

    distribution_effectivity: float
    distribution_effectivity_bonus_per_quality_level: float

    diminishing_returns_profile: list[int]

    module_slots: int
    allowed_modules: list  # List of module types
    effect_area_distance: int
