from collections.abc import Mapping
from dataclasses import dataclass

from .common import ModuleEffect


@dataclass(frozen=True, slots=True)
class Module:
    name: str
    tier: int
    effects: Mapping[ModuleEffect, float]
