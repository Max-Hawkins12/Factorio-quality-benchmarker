from factorio_quality_benchmarker.game.models import Item, Quality

from .models import RecipeConfiguration


def _dominates(
    left: RecipeConfiguration,
    right: RecipeConfiguration,
    product: Item,
    input_quality: Quality,
) -> bool:
    left_metrics = (
        left.metrics.total_per_craft[product],
        left.metrics.total_per_craft_above(input_quality)[product],
        left.metrics.total_per_second[product],
        left.metrics.total_per_second_above(input_quality)[product],
    )

    right_metrics = (
        right.metrics.total_per_craft[product],
        right.metrics.total_per_craft_above(input_quality)[product],
        right.metrics.total_per_second[product],
        right.metrics.total_per_second_above(input_quality)[product],
    )

    return all(
        left >= right for left, right in zip(left_metrics, right_metrics)
    ) and any(left > right for left, right in zip(left_metrics, right_metrics))


def get_recipe_frontier(
    configurations: tuple[RecipeConfiguration, ...],
    product: Item,
    input_quality: Quality,
) -> tuple[RecipeConfiguration, ...]:
    return tuple(
        candidate
        for candidate in configurations
        if not any(
            other is not candidate
            and _dominates(other, candidate, product, input_quality)
            for other in configurations
        )
    )
