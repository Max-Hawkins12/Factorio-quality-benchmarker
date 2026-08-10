from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModuleEffect:
    property: str
    amount: float


@dataclass(frozen=True, slots=True)
class ModuleType:
    name: str
    effect: tuple[ModuleEffect, ...]


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    category: ModuleType
    tier: int

    distribution_effectivity: float
    distribution_effectivity_bonus_per_quality_level: float

    diminishing_returns_profile: list[int]

    module_slots: int
    allowed_modules: list  # List of module types
    effect_area_distance: int
