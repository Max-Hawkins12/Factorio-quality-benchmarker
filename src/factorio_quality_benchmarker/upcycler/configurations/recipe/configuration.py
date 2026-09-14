from factorio_quality_benchmarker.game.engine import (
    calculate_recipe_metrics,
)
from factorio_quality_benchmarker.game.models import Crafter, Item, Quality, Recipe
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    AllowedRecipeEffects,
    MachineConfigurationIndex,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine

from .models import (
    RecipeConfiguration,
    RecipeConfigurationIndex,
)
from .pareto import get_frontier_recipe_candidates, get_legendary_recipe_candidates


def generate_recipe_configurations_for_recipe(
    recipe: Recipe,
    qualities: dict[str, Quality],
    crafters: dict[str, Qualified[Crafter]],
    machine_configuration_cache: dict[QualifiedMachine, MachineConfigurationIndex],
    productivity_research_index: dict[Item, int],
) -> RecipeConfigurationIndex:

    recipe_effects = AllowedRecipeEffects(
        productivity=recipe.allow_productivity,
        quality=recipe.allow_quality,
    )

    valid_machine_configurations = {
        crafter: machine_configuration_cache[crafter][recipe_effects]
        for crafter in crafters.values()
        if crafter in machine_configuration_cache
        and any(category in crafter.entity.categories for category in recipe.categories)
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
                    machine_configuration=configuration.machine_configuration,
                    productivity_research_index=productivity_research_index,
                    normal_quality=qualities["normal"],
                ),
            )
            for configuration in frontier
        )

    return index
