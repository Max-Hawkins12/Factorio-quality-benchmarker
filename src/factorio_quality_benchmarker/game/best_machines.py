import logging
from collections.abc import Callable, Iterable
from typing import TypeVar

from factorio_quality_benchmarker.game.models import (
    Crafter,
    CraftingCategory,
    Miner,
    ResourceCategory,
)

logger = logging.getLogger(__name__)

TCategory = TypeVar("TCategory")
TEntity = TypeVar("TEntity")


def _find_best_per_category[TCategory, TEntity](
    categories: Iterable[TCategory],
    entities: Iterable[TEntity],
    *,
    supports_category: Callable[[TEntity, TCategory], bool],
    module_slots: Callable[[TEntity], int],
    speed: Callable[[TEntity], float],
    logger_message: str,
) -> dict[TCategory, TEntity]:
    entities = tuple(entities)
    best_per_category: dict[TCategory, TEntity] = {}

    for category in categories:
        candidates = tuple(
            entity for entity in entities if supports_category(entity, category)
        )

        for candidate in candidates:
            if all(
                module_slots(candidate) >= module_slots(other)
                and speed(candidate) >= speed(other)
                for other in candidates
            ):
                best_per_category[category] = candidate
                break
        else:
            if candidates:
                raise ValueError(
                    f"No single dominant entity exists for category {category!r}"
                )

    logger.debug("Found the domanant machine for all %s", logger_message)

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
        logger_message="crafting categories",
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
        logger_message="resource categories",
    )
