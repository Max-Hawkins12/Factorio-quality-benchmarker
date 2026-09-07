from dataclasses import dataclass
from typing import Protocol

from factorio_quality_benchmarker.game.models import Quality


class Named(Protocol):
    @property
    def name(self) -> str: ...


@dataclass(frozen=True, slots=True)
class Qualified[T: Named]:
    entity: T
    quality: Quality

    @property
    def name(self) -> str:
        return f"{self.quality.name}-{self.entity.name}"
