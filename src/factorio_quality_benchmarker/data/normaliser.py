from collections.abc import Callable
from typing import Any

type Prototype = dict[str, Any]
type PrototypeCollection = dict[str, Prototype]
type GameData = dict[str, PrototypeCollection]


# Factorio defaults that are missing from the data dump
DEFAULT_RECIPE_CATEGORIES = ["crafting"]
DEFAULT_RESOURCE_CATEGORY = "basic-solid"
NAUVIS_DEFAULT_SURFACE_PROPERTIES: Prototype = {
    "magnetic-field": 90,
    "pressure": 1000,
    "gravity": 10,
}


DESIRED_MODULE_EFFECTS = {"productivity", "quality", "speed"}

EXCLUDED_CRAFTING_MACHINES = {
    "assembling-machine-1",
    "assembling-machine-2",
    "oil-refinery",
}
EXCLUDED_FURNACES = {"stone-furnace", "steel-furnace"}
EXCLUDED_MINERS = {"burner-mining-drill", "pumpjack"}
EXCLUDED_RECIPES = {"biter-egg", "rocket-part"}


def _get_excluded_machines(game_data: GameData):
    """
    Returns the set of machines that should be excluded.
    """

    to_exclude = EXCLUDED_CRAFTING_MACHINES | EXCLUDED_FURNACES | EXCLUDED_MINERS

    if "Space Age" in game_data["metadata"]["metadata"]["active_mods"]:
        to_exclude = to_exclude | {"electric-mining-drill"}

    return to_exclude


def _clean_prototype_noise(game_data: GameData) -> None:
    """
    Removes any prototypes that have names like "*-unknown" or "parameter-*".
    """
    for prototypes in game_data.values():
        for prototype_name, prototype in list(prototypes.items()):
            name = prototype.get("name", "")
            if name.endswith("-unknown") or name.startswith("parameter-"):
                del prototypes[prototype_name]


def _apply_factorio_defaults(game_data: GameData) -> None:
    """
    Add missing default values, which would otherwise be added by the Factrio Engine.
    """

    for recipe in game_data.get("recipes", {}).values():
        if recipe.get("categories") is None:
            recipe["categories"] = DEFAULT_RECIPE_CATEGORIES.copy()

    for resource in game_data.get("resources", {}).values():
        if resource.get("category") is None:
            resource["category"] = DEFAULT_RESOURCE_CATEGORY

    for surface in game_data.get("surfaces", {}).values():
        properties = surface.setdefault("surface_properties", {})

        if properties is None:
            properties = {}
            surface["surface_properties"] = properties

        for property_name, default_value in NAUVIS_DEFAULT_SURFACE_PROPERTIES.items():
            properties.setdefault(property_name, default_value)


def _remove_prototypes(
    prototypes: PrototypeCollection, should_remove: Callable[[Prototype], bool]
) -> None:
    """
    Removes prototypes for which should_remove returns True.
    """
    for prototype_name, prototype in list(prototypes.items()):
        if should_remove(prototype):
            del prototypes[prototype_name]


def _remove_recipes_with_no_item_outputs(game_data: GameData) -> None:
    """
    Removes recipes that do not produce any items.
    """

    recipes = game_data.get("recipes", {})

    _remove_prototypes(
        recipes,
        lambda recipe: (
            not any(
                result.get("type") == "item" for result in recipe.get("results") or []
            )
        ),
    )


def _remove_fluid_resources(game_data: GameData) -> None:
    """
    Removes resources that are of type basic-fluid.
    """

    resources = game_data.get("resources", {})

    _remove_prototypes(
        resources, lambda resource: resource.get("category") == "basic-fluid"
    )


def _remove_fluid_only_miners(game_data: GameData) -> None:
    """
    Removes miners that are for fluid resources.
    """

    miners = game_data.get("miners", {})

    _remove_prototypes(
        miners,
        lambda miner: all(
            category == "basic-fluid"
            for category in miner.get("resource_categories") or []
        ),
    )


def _remove_modules_with_no_desired_effects(game_data: GameData) -> None:
    """
    Removes modules that do not effect productivity, quality, or speed.
    """

    modules = game_data.get("modules", {})

    _remove_prototypes(
        modules,
        lambda module: not (module.get("effect", {}).keys() & DESIRED_MODULE_EFFECTS),
    )


def _remove_crafters_and_furnaces_with_no_quality(game_data: GameData) -> None:
    """
    Removes crafting machines and furnaces which don't support quality.
    """

    for collection_name in ("crafting_machines", "furnaces"):
        machines = game_data.get(collection_name, {})

        _remove_prototypes(
            machines,
            lambda machine: "quality" not in (machine.get("allowed_effects") or []),
        )


def _remove_excluded_machines(game_data: GameData) -> None:
    """
    Removes machines explicitly excluded from the upcycler model.
    """

    for collection_name in ("crafting_machines", "furnaces", "miners"):
        machines = game_data.get(collection_name, {})

        _remove_prototypes(
            machines,
            lambda machine: machine["name"] in _get_excluded_machines(game_data),
        )


def _remove_excluded_recipes(game_data: GameData) -> None:
    """
    Removes recipes explicitly excluded from the upcycler model.
    """

    recipies = game_data.get("recipes", {})

    _remove_prototypes(
        recipies,
        lambda recipe: recipe["name"] in EXCLUDED_RECIPES,
    )


def _remove_materials_not_used_in_recipes(game_data: GameData) -> None:
    """
    Removes items and fluids that are not referenced by any remaining recipe.
    """
    used_items: set[str] = set()
    used_fluids: set[str] = set()

    for recipe in game_data.get("recipes", {}).values():
        for material in (recipe.get("ingredients") or []) + (
            recipe.get("results") or []
        ):
            if material.get("type") == "item":
                used_items.add(material["name"])
            elif material.get("type") == "fluid":
                used_fluids.add(material["name"])

    _remove_prototypes(
        game_data.get("items", {}),
        lambda item: item["name"] not in used_items,
    )

    _remove_prototypes(
        game_data.get("fluids", {}),
        lambda fluid: fluid["name"] not in used_fluids,
    )


def _validate_recipe_machine_coverage(game_data: GameData) -> None:
    """
    Validates that every retained recipe can be crafted by at least one
    retained crafting machine or furnace.
    """
    supported_categories: set[str] = set()

    for collection_name in ("crafting_machines", "furnaces"):
        for machine in game_data.get(collection_name, {}).values():
            supported_categories.update(machine.get("crafting_categories") or [])

    missing_recipes: list[str] = []

    for recipe_name, recipe in game_data.get("recipes", {}).items():
        recipe_categories = recipe.get("categories") or []

        if not any(category in supported_categories for category in recipe_categories):
            missing_recipes.append(f"{recipe_name} ({', '.join(recipe_categories)})")

    if missing_recipes:
        raise ValueError(
            "Recipes have no compatible retained crafting machine: "
            + ", ".join(sorted(missing_recipes))
        )


def normalise_game_data(game_data: GameData) -> GameData:

    _clean_prototype_noise(game_data)

    _apply_factorio_defaults(game_data)

    _remove_recipes_with_no_item_outputs(game_data)
    _remove_fluid_resources(game_data)
    _remove_fluid_only_miners(game_data)

    _remove_modules_with_no_desired_effects(game_data)
    _remove_crafters_and_furnaces_with_no_quality(game_data)

    _remove_excluded_machines(game_data)
    _remove_excluded_recipes(game_data)

    _remove_materials_not_used_in_recipes(game_data)

    _validate_recipe_machine_coverage(game_data)

    return game_data
