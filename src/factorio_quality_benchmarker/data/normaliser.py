import logging
from collections.abc import Callable

from .types import ParsedGameData, Prototype, PrototypeCollection

logger = logging.getLogger(__name__)

# Factorio defaults that are missing from the data dump
DEFAULT_RECIPE_CATEGORIES = ["crafting"]
DEFAULT_RESOURCE_CATEGORY = "basic-solid"
DEFAULT_ALLOWED_EFFECTS = [
    "consumption",
    "speed",
    "productivity",
    "pollution",
    "quality",
]
NAUVIS_DEFAULT_SURFACE_PROPERTIES: Prototype = {
    "magnetic-field": 90,
    "solar-power": 100,
    "pressure": 1000,
    "gravity": 10,
}


def _apply_factorio_defaults(game_data: ParsedGameData) -> None:
    """
    Add missing default values, which would otherwise be added by the Factrio Engine.
    """

    for recipe in game_data.get("recipes", {}).values():
        if recipe.get("categories") is None:
            recipe["categories"] = DEFAULT_RECIPE_CATEGORIES.copy()

    for resource in game_data.get("resources", {}).values():
        if resource.get("category") is None:
            resource["category"] = DEFAULT_RESOURCE_CATEGORY

    for miner in game_data.get("miners", {}).values():
        if miner.get("allowed_effects") is None:
            miner["allowed_effects"] = DEFAULT_ALLOWED_EFFECTS

    for surface in game_data.get("surfaces", {}).values():
        properties = surface.setdefault("surface_properties", {})

        if properties is None:
            properties = {}
            surface["surface_properties"] = properties

        for property_name, default_value in NAUVIS_DEFAULT_SURFACE_PROPERTIES.items():
            properties.setdefault(property_name, default_value)

    logger.debug("Added missing default values")


def _normalise_resource_result(game_data: ParsedGameData) -> None:
    """
    Adds a standard results dict to item resources,
    which only have a result field in the data dump
    """
    for resource in game_data.get("resources", {}).values():
        if "result" in resource["minable"]:
            resource["minable"]["results"] = [
                {
                    "type": "item",
                    "name": resource["minable"]["result"],
                    "amount": 1,
                }
            ]

    logger.debug("Normalised resource results field")


# Helper methods
def _remove_prototypes(
    prototypes: PrototypeCollection,
    should_remove: Callable[[Prototype], bool],
) -> int:
    """
    Remove prototypes for which should_remove returns True.
    Returns the number of entries removed.
    """
    removed = 0

    for prototype_name, prototype in list(prototypes.items()):
        if should_remove(prototype):
            del prototypes[prototype_name]
            removed += 1

    return removed


# Cleaning methods
def _remove_prototype_placeholders(game_data: ParsedGameData) -> None:
    """
    Removes any prototypes that have names like "*-unknown" or "parameter-*".
    """
    removed = 0

    for prototypes in game_data.values():
        removed += _remove_prototypes(
            prototypes,
            lambda prototype: prototype.get("name", "").endswith("-unknown"),
        )

    logger.debug("Removed %d prototype placeholders", removed)


def _remove_empty_recipes(game_data: ParsedGameData) -> None:
    """
    Remove recipes that have neither ingredients nor results.
    """
    recipes = game_data.get("recipes", {})

    removed = _remove_prototypes(
        recipes,
        lambda recipe: (
            not (recipe.get("ingredients") or []) and not (recipe.get("results") or [])
        ),
    )

    logger.debug("Removed %d recipes with no ingredients and no results", removed)


def _remove_recipes_with_missing_materials(game_data: ParsedGameData) -> None:
    """
    Remove recipes that reference an item or fluid that is absent from the parsed material collections.
    """
    item_names = set(game_data.get("items", {}))
    fluid_names = set(game_data.get("fluids", {}))

    def has_missing_material(recipe: Prototype) -> bool:
        materials = (recipe.get("ingredients") or []) + (recipe.get("results") or [])

        for material in materials:
            material_type = material.get("type")
            material_name = material.get("name")

            if material_type == "item" and material_name not in item_names:
                return True

            if material_type == "fluid" and material_name not in fluid_names:
                return True

        return False

    removed = _remove_prototypes(
        game_data.get("recipes", {}),
        has_missing_material,
    )

    logger.debug("Removed %d recipes referencing missing materials", removed)


def _count_prototypes(game_data: ParsedGameData) -> int:
    """
    Returns the total number of prototypes in the data.
    """

    return sum(len(prototypes) for prototypes in game_data.values())


def normalise_game_data(game_data: ParsedGameData) -> ParsedGameData:
    """
    Apply Factorio defaults and perform conservative data cleanup:

    - add implicit Factorio default values;
    - normalise equivalent data representations;
    - remove placeholder prototypes;
    - remove structurally empty recipes;
    - remove recipes referencing missing materials.
    """
    start_count = _count_prototypes(game_data)
    logger.debug("Found %d prototypes", start_count)

    _apply_factorio_defaults(game_data)
    _normalise_resource_result(game_data)

    _remove_prototype_placeholders(game_data)

    _remove_empty_recipes(game_data)
    _remove_recipes_with_missing_materials(game_data)

    end_count = _count_prototypes(game_data)

    logger.info(
        "Normalisation complete: %d prototypes removed, %d retained",
        start_count - end_count,
        end_count,
    )

    return game_data
