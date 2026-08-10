from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Surface:
    name: str
    magnetic_field: float
    gravity: float
    pressure: float
