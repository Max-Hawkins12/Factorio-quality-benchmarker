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


def _quality_output(
    input_quality: Quality,
    product_amount: float,
    machine_configuration: MachineConfiguration,
) -> QualityAmounts:
    if (
        input_quality.next_probability is None
        or input_quality.chain_probability is None
        or input_quality.next is None
    ):
        return QualityAmounts({input_quality: product_amount})

    quality_chance = _quality_bonus(machine_configuration)

    quality_amounts: dict[Quality, float] = {
        input_quality: product_amount * (1.0 - quality_chance)
    }

    next_quality = input_quality.next
    continuing_probability = quality_chance * input_quality.next_probability

    while next_quality is not None:
        if next_quality.next is None:
            # Highest quality: everything that reaches it stays here.
            quality_amounts[next_quality] = product_amount * continuing_probability
            break

        chain_probability = (
            next_quality.chain_probability
            if next_quality.chain_probability is not None
            else 0.0
        )

        quality_amounts[next_quality] = (
            product_amount * continuing_probability * (1.0 - chain_probability)
        )

        continuing_probability *= chain_probability
        next_quality = next_quality.next

    return QualityAmounts(quality_amounts)


def _calculate_output_per_craft(
    recipe: Recipe,
    input_quality: Quality,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
    normal_quality: Quality,
) -> dict[Material, QualityAmounts]:

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
        product.material: (
            _quality_output(
                input_quality,
                product.amount * productivity,
                machine_configuration,
            )
            if isinstance(product.material, Item)
            else QualityAmounts({normal_quality: product.amount * productivity})
        )
        for product in recipe.products
    }


def _calculate_crafts_per_second(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
) -> float:

    return (
        get_qualified_crafting_speed(crafter)
        * (1.0 + _speed_bonus(machine_configuration))
        / recipe.energy_required
    )


def _calculate_output_per_second(
    recipe: Recipe,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    output_per_craft: dict[Material, QualityAmounts],
) -> dict[Material, QualityAmounts]:

    crafts_per_second = _calculate_crafts_per_second(
        recipe, crafter, machine_configuration
    )

    return {
        material: amounts.scale(crafts_per_second)
        for material, amounts in output_per_craft.items()
    }


def get_recipe_metrics(
    recipe: Recipe,
    input_quality: Quality,
    crafter: Qualified[Crafter],
    machine_configuration: MachineConfiguration,
    productivity_research_index: dict[Item, int],
    normal_quality: Quality,
) -> RecipeMetrics:
    output_per_craft = _calculate_output_per_craft(
        recipe,
        input_quality,
        crafter,
        machine_configuration,
        productivity_research_index,
        normal_quality,
    )

    output_per_second = _calculate_output_per_second(
        recipe,
        crafter,
        machine_configuration,
        output_per_craft,
    )

    return RecipeMetrics(
        output_per_craft=output_per_craft,
        output_per_second=output_per_second,
    )
