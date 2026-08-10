from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CraftingCategory:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Crafting category cannot be empty")
