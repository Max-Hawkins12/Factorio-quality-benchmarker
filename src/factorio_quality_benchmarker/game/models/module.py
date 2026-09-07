from collections.abc import Mapping
from dataclasses import dataclass

from .common import ModuleEffect


@dataclass(frozen=True, slots=True)
class ModuleCategory:
    type: str


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    tier: int
    category: ModuleCategory
    effects: Mapping[ModuleEffect, float]


EMPTY_MODULE = Module(
    name="empty",
    tier=0,
    category=ModuleCategory(type="empty"),
    effects={},
)
