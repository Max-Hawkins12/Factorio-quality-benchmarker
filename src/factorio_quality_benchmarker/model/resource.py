from dataclasses import dataclass

from .common import ResourceCategory
from .material import Product


@dataclass(frozen=True, slots=True)
class Resource:
    name: str

    category: ResourceCategory

    mining_time: float
    product: tuple[Product, ...]
