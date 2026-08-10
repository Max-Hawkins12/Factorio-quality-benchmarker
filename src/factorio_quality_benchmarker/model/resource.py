from dataclasses import dataclass

from . import Material


@dataclass(frozen=True, slots=True)
class Resource:
    name: str

    category: (
        str  # Maybe redunant, fluids are ignored, and only the big miner will be used
    )

    mining_time: float
    result: Material
