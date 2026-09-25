from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Quality:
    name: str

    level: int
    next: Quality | None

    next_probability: float | None
    chain_probability: float | None

