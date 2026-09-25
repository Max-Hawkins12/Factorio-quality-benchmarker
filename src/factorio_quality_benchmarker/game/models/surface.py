from collections.abc import Mapping
from dataclasses import dataclass

from .common import SurfaceProperty


@dataclass(frozen=True, slots=True)
class Surface:
    name: str
    properties: Mapping[SurfaceProperty, float]
