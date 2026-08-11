from dataclasses import dataclass

from .common import ModuleCategory, ModuleEffect


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    category: ModuleCategory
    tier: int
    effects: tuple[tuple[ModuleEffect, float], ...]
