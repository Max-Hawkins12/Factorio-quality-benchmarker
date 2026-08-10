from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Miner:
    name: str

    mining_speed: float
    module_slots: int
    allowed_modules: list  # List of module types

    maximum_beacons: int
