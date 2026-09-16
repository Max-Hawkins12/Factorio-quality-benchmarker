from collections.abc import Mapping
from dataclasses import dataclass, field

from factorio_quality_benchmarker.game.engine import calculate_recipe_metrics
from factorio_quality_benchmarker.game.models import Crafter, Item, Quality, Recipe
from factorio_quality_benchmarker.optimiser.configurations.cache import get_from_cache
from factorio_quality_benchmarker.optimiser.configurations.machine import (
    AllowedRecipeEffects,
    MachineConfigurationCache,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .models import RecipeConfiguration, RecipeConfigurationIndex
from .pareto import get_frontier_recipe_candidates, get_legendary_recipe_candidates


def _generate_recipe_configurations_for_recipe(
    recipe: Recipe,
    qualities: Mapping[str, Quality],
    crafters: Mapping[str, Qualified[Crafter]],
    productivity_research_index: Mapping[Item, int],
    machine_configuration_cache: MachineConfigurationCache,
) -> RecipeConfigurationIndex:

    recipe_effects = AllowedRecipeEffects(
        productivity=recipe.allow_productivity,
        quality=recipe.allow_quality,
    )

    valid_machine_configurations = {
        crafter: machine_configuration_cache.get(crafter)[recipe_effects]
        for crafter in crafters.values()
        if any(category in crafter.entity.categories for category in recipe.categories)
    }

    normal_frontier = get_frontier_recipe_candidates(
        recipe,
        valid_machine_configurations,
        productivity_research_index,
    )

    index: RecipeConfigurationIndex = {}

    for quality in qualities.values():
        frontier = normal_frontier

        if quality == qualities["legendary"]:
            frontier = get_legendary_recipe_candidates(normal_frontier)

        index[quality] = tuple(
            RecipeConfiguration(
                crafter=configuration.crafter,
                machine_configuration=configuration.machine_configuration,
                metrics=calculate_recipe_metrics(
                    recipe=recipe,
                    input_quality=quality,
                    crafter=configuration.crafter,
                    machine_effects=configuration.machine_configuration.effects,
                    productivity_research_index=productivity_research_index,
                    normal_quality=qualities["normal"],
                ),
            )
            for configuration in frontier
        )

    return index


@dataclass(slots=True)
class RecipeConfigurationCache:
    qualities: Mapping[str, Quality]
    crafters: Mapping[str, Qualified[Crafter]]
    productivity_research_index: Mapping[Item, int]

    machine_cache: MachineConfigurationCache

    _cache: dict[
        Recipe,
        RecipeConfigurationIndex,
    ] = field(default_factory=dict)

    def get(self, recipe: Recipe) -> RecipeConfigurationIndex:
        return get_from_cache(
            cache=self._cache,
            key=recipe,
            calculate=lambda: _generate_recipe_configurations_for_recipe(
                recipe=recipe,
                qualities=self.qualities,
                crafters=self.crafters,
                productivity_research_index=self.productivity_research_index,
                machine_configuration_cache=self.machine_cache,
            ),
        )
