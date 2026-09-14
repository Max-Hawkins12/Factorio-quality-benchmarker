from collections.abc import Mapping

from factorio_quality_benchmarker.game.models import (
    Crafter,
    Item,
    Material,
    Quality,
    Recipe,
)
from factorio_quality_benchmarker.upcycler.configurations.machine import (
    MachineConfiguration,
)
from factorio_quality_benchmarker.upcycler.simulation import Qualified

from .constants import MAXIMUM_PRODUCTIVITY
from .models import QualityAmounts, RecipeMetrics
from .quality import get_qualified_crafting_speed


# Determine overall bonuses
def _productivity_bonus(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
) -> float:

    research_productivity = 0.0

    if len(recipe.product_items) == 1:
        product = recipe.product_items[0]

        research_productivity = productivity_research_index.get(product, 0.0) / 10

    return (
        machine_configuration.effects.productivity
        + crafter.entity.inherent_productivity
        + research_productivity
    )


def _quality_bonus(machine_configuration: MachineConfiguration) -> float:
    return max(machine_configuration.effects.quality, 0.0)


def _speed_bonus(machine_configuration: MachineConfiguration) -> float:
    return machine_configuration.effects.speed


# Output amount calculations
def _calculate_total_output_per_craft(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
) -> Mapping[Material, float]:

    productivity = 1.0 + min(
        _productivity_bonus(
            recipe,
            crafter,
            machine_configuration,
            productivity_research_index,
        ),
        MAXIMUM_PRODUCTIVITY,
    )

    return {
        product.material: product.amount * productivity for product in recipe.products
    }


def _calculate_total_output_per_second(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    output_per_craft: Mapping[Material, float],
) -> Mapping[Material, float]:

    crafts_per_second = (
        get_qualified_crafting_speed(crafter)
        * (1.0 + _speed_bonus(machine_configuration))
        / recipe.energy_required
    )

    return {
        material: crafts_per_second * amount
        for material, amount in output_per_craft.items()
    }


def _apply_quality_distribution(
    input_quality: Quality,
    product_amount: float,
    machine_configuration: MachineConfiguration,
) -> QualityAmounts:
    if (
        input_quality.next_probability is None
        or input_quality.chain_probability is None
        or input_quality.next is None
    ):
        return QualityAmounts({input_quality: round(product_amount, 12)})

    quality_chance = _quality_bonus(machine_configuration)

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


def _recipe_metrics(
    total_per_craft: Mapping[Material, float],
    total_per_second: Mapping[Material, float],
    input_quality: Quality,
    machine_configuration: MachineConfiguration,
    normal_quality: Quality,
) -> RecipeMetrics:
    return RecipeMetrics(
        output_per_craft={
            material: _apply_quality_distribution(
                input_quality, amount, machine_configuration
            )
            if isinstance(material, Item)
            else QualityAmounts({normal_quality: amount})
            for material, amount in total_per_craft.items()
        },
        output_per_second={
            material: _apply_quality_distribution(
                input_quality, amount, machine_configuration
            )
            if isinstance(material, Item)
            else QualityAmounts({normal_quality: amount})
            for material, amount in total_per_second.items()
        },
    )


# Public API
def calculate_recipe_metrics(
    recipe: Recipe,
    input_quality: Quality,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
    normal_quality: Quality,
) -> RecipeMetrics:
    total_per_craft = _calculate_total_output_per_craft(
        recipe,
        crafter,
        machine_configuration,
        productivity_research_index,
    )

    total_per_second = _calculate_total_output_per_second(
        recipe,
        crafter,
        machine_configuration,
        total_per_craft,
    )

    return _recipe_metrics(
        total_per_craft,
        total_per_second,
        input_quality,
        machine_configuration,
        normal_quality,
    )


def recalculate_recipe_metrics(
    input_quality: Quality,
    machine_configuration: MachineConfiguration,
    recipe_metrics: RecipeMetrics,
    normal_quality: Quality,
) -> RecipeMetrics:

    return _recipe_metrics(
        recipe_metrics.total_per_craft,
        recipe_metrics.total_per_second,
        input_quality,
        machine_configuration,
        normal_quality,
    )


def calculate_recipe_objectives(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
) -> tuple[float, float, float, float]:
    """This is a cheap operation for calculating an estimate of the recipe metrics"""
    productivity = 1.0 + min(
        _productivity_bonus(
            recipe,
            crafter,
            machine_configuration,
            productivity_research_index,
        ),
        MAXIMUM_PRODUCTIVITY,
    )

    total_per_craft = recipe.products[0].amount * productivity

    crafts_per_second = (
        get_qualified_crafting_speed(crafter)
        * (1.0 + _speed_bonus(machine_configuration))
        / recipe.energy_required
    )

    total_per_second = total_per_craft * crafts_per_second

    quality = _quality_bonus(machine_configuration)

    return (
        round(total_per_craft, 12),
        round(total_per_craft * quality, 12),
        round(total_per_second, 12),
        round(total_per_second * quality, 12),
    )
