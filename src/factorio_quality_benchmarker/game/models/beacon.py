from dataclasses import dataclass

from .common import ModuleMachine


@dataclass(frozen=True, slots=True)
class Beacon(ModuleMachine):
    name: str

    distribution_effectivity: float
    distribution_effectivity_bonus_per_quality_level: float
    diminishing_returns_profile: tuple[float, ...]

    effect_range: int
