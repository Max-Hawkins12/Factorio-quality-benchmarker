from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MachineEffects:
    speed: float
    productivity: float
    quality: float
