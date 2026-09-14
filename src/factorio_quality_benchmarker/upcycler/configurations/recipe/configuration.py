"""
Take the machine configurations dict and the recipes.


Produce a recipe configurations which optimise for quality/s, quality/craft, total/craft, total/s

quality/craft
    quality disabled:
        all configs equivalent (0 quality output)

    quality enabled, productivity disabled:
        maximise quality

    quality enabled, productivity enabled:
        quality/productivity trade-off

quality/s
    quality disabled:
        all configs equivalent (0 quality output)

    quality enabled, productivity disabled:
        quality/speed trade-off

    quality enabled, productivity enabled:
        quality/productivity/speed trade-off

total/craft
    productivity disabled:
        all configs equivalent

    productivity enabled:
        maximise productivity

total/s
    productivity disabled:
        maximise speed

    productivity enabled:
        speed/productivity trade-off

"""

from factorio_quality_benchmarker.game.engine import (
    calculate_recipe_metrics,
    recalculate_recipe_metrics,
)
from factorio_quality_benchmarker.game.models import Crafter, Item, Quality, Recipe
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    AllowedRecipeEffects,
    MachineConfiguration,
    MachineConfigurationIndex,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified, QualifiedMachine

from .models import RecipeConfiguration, RecipeConfigurationIndex
from .pareto import get_recipe_frontier


def _generate_recipe_configurations(
    recipe: Recipe,
    input_quality: Quality,
    machine_configurations: dict[Qualified[Crafter], tuple[MachineConfiguration, ...]],
    productivity_research_index: dict[Item, int],
    normal_quality: Quality,
) -> tuple[RecipeConfiguration, ...]:

    return tuple(
        RecipeConfiguration(
            crafter=crafter,
            machine_configuration=configuration,
            metrics=calculate_recipe_metrics(
                recipe,
                input_quality,
                crafter,
                configuration,
                productivity_research_index,
                normal_quality,
            ),
        )
        for crafter, configurations in machine_configurations.items()
        for configuration in configurations
    )


def generate_recipe_configurations_for_recipe(
    recipe: Recipe,
    qualities: dict[str, Quality],
    crafters: dict[str, Qualified[Crafter]],
    machine_configuration_cache: dict[QualifiedMachine, MachineConfigurationIndex],
    productivity_research_index: dict[Item, int],
) -> RecipeConfigurationIndex:

    if not recipe.product_items:
        raise ValueError(f"Recipe {recipe.name} has no item products")
    # All products have the same frontier configurations, so only consider the first one
    frontier_product = recipe.product_items[0]

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

    normal = qualities["normal"]

    normal_candidates = _generate_recipe_configurations(  # Missing frontier algorithm
        recipe=recipe,
        input_quality=normal,
        machine_configurations=valid_machine_configurations,
        productivity_research_index=productivity_research_index,
        normal_quality=normal,
    )

    normal_frontier = get_recipe_frontier(normal_candidates, frontier_product, normal)

    index: RecipeConfigurationIndex = {normal: normal_frontier}

    for quality in qualities.values():
        if quality == normal:
            continue

        index[quality] = tuple(
            RecipeConfiguration(
                crafter=configuration.crafter,
                machine_configuration=configuration.machine_configuration,
                metrics=recalculate_recipe_metrics(
                    input_quality=quality,
                    machine_configuration=configuration.machine_configuration,
                    recipe_metrics=configuration.metrics,
                    normal_quality=normal,
                ),
            )
            for configuration in normal_frontier
        )

    index[qualities["legendary"]] = get_recipe_frontier(
        index[qualities["legendary"]], frontier_product, qualities["legendary"]
    )

    return index
