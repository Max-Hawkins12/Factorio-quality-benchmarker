from factorio_quality_benchmarker.model import CraftingCategory, Material, Recipe

from .models import RecipeIndex


def generate_recipe_index(
    materials: dict[str, Material],
    recipes: dict[str, Recipe],
    crafting_categories: dict[str, CraftingCategory],
) -> RecipeIndex:
    """
    Returns an index of all recipes by the materials they consume and produce.

    Recycling recipes are indexed separately from crafting recipes.
    """
    recycling_category = crafting_categories["recycling"]

    producers: dict[Material, list[Recipe]] = {
        material: [] for material in materials.values()
    }

    consumers: dict[Material, list[Recipe]] = {
        material: [] for material in materials.values()
    }

    recycler_consumers: dict[Material, Recipe] = {}

    recycler_producers: dict[Material, list[Recipe]] = {
        material: [] for material in materials.values()
    }

    for recipe in recipes.values():
        if recycling_category in recipe.categories:
            if len(recipe.ingredients) != 1:
                raise ValueError(
                    f"A recycling recipe {recipe.name} has "
                    f"{len(recipe.ingredients)} ingredients. "
                    "Recycling recipes must have 1 ingredient."
                )

            recycled_material = recipe.ingredients[0].material

            if recycled_material in recycler_consumers:
                raise ValueError(
                    f"Multiple recycling recipes found for {recycled_material.name}"
                )

            recycler_consumers[recycled_material] = recipe

            for product in recipe.products:
                recycler_producers[product.material].append(recipe)

            continue

        for ingredient in recipe.ingredients:
            consumers[ingredient.material].append(recipe)

        for product in recipe.products:
            producers[product.material].append(recipe)

    crafter_producers = {
        material: tuple(material_recipes)
        for material, material_recipes in producers.items()
    }

    crafter_consumers = {
        material: tuple(material_recipes)
        for material, material_recipes in consumers.items()
    }

    recycler_producers_index = {
        material: tuple(material_recipes)
        for material, material_recipes in recycler_producers.items()
    }

    return RecipeIndex(
        crafter_producers_by_material=crafter_producers,
        crafter_consumers_by_material=crafter_consumers,
        recycler_producers_by_material=recycler_producers_index,
        recycler_consumers_by_material=recycler_consumers,
    )
