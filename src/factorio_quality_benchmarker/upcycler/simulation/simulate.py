from collections.abc import Mapping

from factorio_quality_benchmarker.game import GameData
from factorio_quality_benchmarker.game.models import Item, Quality, Recipe

from .constants import UNCRAFTABLE_ITEMS
from .models import (
    Named,
    ProductivityResearchLevels,
    Qualified,
    QualifiedIndex,
    RunConfiguration,
    SimulationContext,
)


def _apply_quality[T: Named](
    entities: Mapping[str, T],
    qualities: tuple[Quality, ...],
) -> QualifiedIndex[Qualified[T]]:

    return {
        quality: {name: Qualified(entity, quality) for name, entity in entities.items()}
        for quality in qualities
    }


def _remove_uncraftable_items(items: Mapping[str, Item]) -> Mapping[str, Item]:
    return {name: item for name, item in items.items() if name not in UNCRAFTABLE_ITEMS}


def _remove_uncraftable_recipes(recipes: Mapping[str, Recipe]) -> Mapping[str, Recipe]:
    return {
        name: recipe
        for name, recipe in recipes.items()
        if name not in UNCRAFTABLE_ITEMS
        or name.removesuffix("-recycling") not in UNCRAFTABLE_ITEMS
    }


def _get_productivity_level_index(
    items: Mapping[str, Item],
    productivity_levels: ProductivityResearchLevels,
) -> Mapping[Item, int]:
    return {
        items["processing-unit"]: productivity_levels.processing_unit_level,
        items["low-density-structure"]: productivity_levels.low_density_structure_level,
        items["steel-plate"]: productivity_levels.steel_level,
        items["plastic-bar"]: productivity_levels.plastic_bar_level,
        items["rocket-fuel"]: productivity_levels.rocket_fuel_level,
    }


def build_simulation_context(
    game_data: GameData,
    run_config: RunConfiguration,
) -> SimulationContext:

    qualities = tuple(game_data.qualities.values())
    valid_items = _remove_uncraftable_items(game_data.items)

    return SimulationContext(
        game_data=game_data,
        run_config=run_config,
        productivity_research_index=_get_productivity_level_index(
            valid_items,
            run_config.productivity_levels,
        ),
        items=valid_items,
        recipes=_remove_uncraftable_recipes(game_data.recipes),
        items_by_quality=_apply_quality(valid_items, qualities),
        crafters_by_quality=_apply_quality(game_data.crafters, qualities),
        miners_by_quality=_apply_quality(game_data.miners, qualities),
        modules_by_quality=_apply_quality(game_data.modules, qualities),
        beacons_by_quality=_apply_quality(game_data.beacons, qualities),
    )
