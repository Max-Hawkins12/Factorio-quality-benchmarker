from collections.abc import Callable, Iterable
from typing import TypeVar

from factorio_quality_benchmarker.game.models import (
    Crafter,
    CraftingCategory,
    Miner,
    ResourceCategory,
)

TCategory = TypeVar("TCategory")
TEntity = TypeVar("TEntity")


def _find_best_per_category[TCategory, TEntity](
    categories: Iterable[TCategory],
    entities: Iterable[TEntity],
    *,
    supports_category: Callable[[TEntity, TCategory], bool],
    module_slots: Callable[[TEntity], int],
    speed: Callable[[TEntity], float],
) -> dict[TCategory, TEntity]:
    best_per_category: dict[TCategory, TEntity] = {}

    entities = tuple(entities)

    for category in categories:
        best: TEntity | None = None

        for entity in entities:
            if not supports_category(entity, category):
                continue

            if best is None or (
                module_slots(entity) >= module_slots(best)
                and speed(entity) >= speed(best)
            ):
                best = entity

        if best is not None:
            best_per_category[category] = best

    return best_per_category


def find_best_crafter_per_category(
    crafting_categories: dict[str, CraftingCategory],
    crafters: dict[str, Crafter],
) -> dict[CraftingCategory, Crafter]:
    return _find_best_per_category(
        crafting_categories.values(),
        crafters.values(),
        supports_category=lambda crafter, category: category in crafter.categories,
        module_slots=lambda crafter: crafter.module_slots,
        speed=lambda crafter: crafter.crafting_speed,
    )


def find_best_miner_per_category(
    resource_categories: dict[str, ResourceCategory],
    miners: dict[str, Miner],
) -> dict[ResourceCategory, Miner]:
    return _find_best_per_category(
        resource_categories.values(),
        miners.values(),
        supports_category=lambda miner, category: category in miner.resource_categories,
        module_slots=lambda miner: miner.module_slots,
        speed=lambda miner: miner.mining_speed,
    )
