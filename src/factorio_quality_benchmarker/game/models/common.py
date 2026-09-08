from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CraftingCategory:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Crafting category cannot be empty")


@dataclass(frozen=True, slots=True)
class ModuleEffect:
    effect: str

    def __post_init__(self) -> None:
        if not self.effect.strip():
            raise ValueError("Module effect cannot be empty")


@dataclass(frozen=True, slots=True)
class ResourceCategory:
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Resource category cannot be empty")


@dataclass(frozen=True, slots=True)
class SurfaceProperty:
    property: str

    def __post_init__(self) -> None:
        if not self.property.strip():
            raise ValueError("Surface property cannot be empty")


@dataclass(frozen=True, slots=True)
class ModuleMachine:
    """A parent class for any machine which accepts module and beacon effects"""

    module_slots: int
    allowed_effects: frozenset[ModuleEffect]
    width: int
    height: int
