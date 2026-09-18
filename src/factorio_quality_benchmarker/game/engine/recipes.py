from collections.abc import Mapping

from factorio_quality_benchmarker.game.models import (
    Crafter,
    Fluid,
    Item,
    Material,
    Quality,
    Recipe,
)
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .constants import MAXIMUM_PRODUCTIVITY
from .models import MachineEffects, QualityAmounts, RecipeMetrics
from .quality import get_qualified_crafting_speed


# Determine overall bonuses
def productivity_bonus(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_effects: MachineEffects,
    productivity_research_index: Mapping[Item, int],
) -> float:

    research_productivity = 0.0

    if len(recipe.product_items) == 1:
        product = recipe.product_items[0]

        research_productivity = productivity_research_index.get(product, 0.0) / 10

    return (
        machine_effects.productivity
        + crafter.entity.inherent_productivity
        + research_productivity
    )


def quality_bonus(machine_effects: MachineEffects) -> float:
    return max(machine_effects.quality, 0.0)


def speed_bonus(machine_effects: MachineEffects) -> float:
    return machine_effects.speed


# Output amount calculations
def _calculate_total_output_per_craft(
    recipe: Recipe,
    productivity_bonus: float,
) -> Mapping[Material, float]:

    multiplier_per_craft = 1.0 + min(productivity_bonus, MAXIMUM_PRODUCTIVITY)

    return {
        product.material: product.amount * multiplier_per_craft
        for product in recipe.products
    }


def _calculate_crafts_per_second(
    recipe: Recipe,
    speed_bonus: float,
    crafter: Qualified[Crafter],
) -> float:
    return (
        get_qualified_crafting_speed(crafter)
        * (1.0 + speed_bonus)
        / recipe.energy_required
    )


def _calculate_total_output_per_second(
    crafts_per_second: float,
    output_per_craft: Mapping[Material, float],
) -> Mapping[Material, float]:
    return {
        material: amount * crafts_per_second
        for material, amount in output_per_craft.items()
    }


def _apply_quality_distribution(
    input_quality: Quality,
    quality_bonus: float,
    product_amount: float,
) -> QualityAmounts:
    if (
        input_quality.next_probability is None
        or input_quality.chain_probability is None
        or input_quality.next is None
    ):
        return QualityAmounts({input_quality: round(product_amount, 12)})

    quality_chance = quality_bonus

    quality_amounts: dict[Quality, float] = {
        input_quality: product_amount * (1.0 - quality_chance)
    }

    next_quality = input_quality.next
    continuing_probability = quality_chance * input_quality.next_probability

    while next_quality is not None:
        if next_quality.next is None:
            # Highest quality: everything that reaches it stays here.
            quality_amounts[next_quality] = round(
                product_amount * continuing_probability, 12
            )
            break

        chain_probability = (
            next_quality.chain_probability
            if next_quality.chain_probability is not None
            else 0.0
        )

        quality_amounts[next_quality] = round(
            product_amount * continuing_probability * (1.0 - chain_probability), 12
        )

        continuing_probability *= chain_probability
        next_quality = next_quality.next

    return QualityAmounts(quality_amounts)


# Input amount calculations
def _calculate_total_input_per_craft(
    recipe: Recipe,
    input_quality: Quality,
    normal_quality: Quality,
) -> Mapping[Material, QualityAmounts]:

    inputs = {}

    for ingredient in recipe.ingredients:
        quality = input_quality

        if isinstance(ingredient.material, Fluid):
            quality = normal_quality

        inputs[ingredient.material] = QualityAmounts({quality: ingredient.amount})

    return inputs


def _calculate_total_input_per_second(
    recipe: Recipe,
    crafts_per_second: float,
    input_quality: Quality,
    normal_quality: Quality,
) -> Mapping[Material, QualityAmounts]:

    inputs = {}

    for ingredient in recipe.ingredients:
        quality = input_quality

        if isinstance(ingredient.material, Fluid):
            quality = normal_quality

        inputs[ingredient.material] = QualityAmounts(
            {quality: ingredient.amount * crafts_per_second}
        )

    return inputs


# Public API
def calculate_recipe_metrics(
    recipe: Recipe,
    input_quality: Quality,
    crafter: Qualified[Crafter],
    machine_effects: MachineEffects,
    productivity_research_index: Mapping[Item, int],
    normal_quality: Quality,
) -> RecipeMetrics:

    quality = quality_bonus(machine_effects)
    speed = speed_bonus(machine_effects)
    productivity = productivity_bonus(
        recipe,
        crafter,
        machine_effects,
        productivity_research_index,
    )

    crafts_per_second = _calculate_crafts_per_second(recipe, speed, crafter)

    total_per_craft = _calculate_total_output_per_craft(recipe, productivity)

    total_per_second = _calculate_total_output_per_second(
        crafts_per_second,
        total_per_craft,
    )

    return RecipeMetrics(
        output_per_craft={
            material: _apply_quality_distribution(input_quality, quality, amount)
            if isinstance(material, Item)
            else QualityAmounts({normal_quality: amount})
            for material, amount in total_per_craft.items()
        },
        output_per_second={
            material: _apply_quality_distribution(input_quality, quality, amount)
            if isinstance(material, Item)
            else QualityAmounts({normal_quality: amount})
            for material, amount in total_per_second.items()
        },
        input_per_craft=_calculate_total_input_per_craft(
            recipe, input_quality, normal_quality
        ),
        input_per_second=_calculate_total_input_per_second(
            recipe, crafts_per_second, input_quality, normal_quality
        ),
        quality_bonus=quality,
        productivity_bonus=productivity,
        crafts_per_second=crafts_per_second,
    )
