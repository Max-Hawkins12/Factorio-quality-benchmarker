from dataclasses import dataclass

from .common import ModuleEffect


@dataclass(frozen=True, slots=True)
class Beacon:
    name: str

    distribution_effectivity: float
    diminishing_returns_profile: tuple[int, ...]

    module_slots: int
    allowed_effects: frozenset[ModuleEffect]

    effect_range: int
    width: int
    height: int
