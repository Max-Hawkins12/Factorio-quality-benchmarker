import logging
from collections.abc import Callable

from .types import ParsedGameData, Prototype, PrototypeCollection
from .utils import has_space_age

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

# Machines that are strictly superseded for the simulator's purposes.
REDUNDANT_CRAFTING_MACHINES = {
    "assembling-machine-1",
    "assembling-machine-2",
}

REDUNDANT_FURNACES = {
    "stone-furnace",
    "steel-furnace",
}

REDUNDANT_MINERS = {
    "burner-mining-drill",
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


def _get_redundant_machines(game_data: ParsedGameData) -> set[str]:
    """
    Return machines that are directly superseded by another retained machine.

    The electric mining drill is only redundant when Space Age is enabled, because the big mining drill then provides the direct upgrade.
    """
    redundant = REDUNDANT_CRAFTING_MACHINES | REDUNDANT_FURNACES | REDUNDANT_MINERS

    if has_space_age(game_data):
        redundant = redundant | {"electric-mining-drill"}

    return redundant


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


def _remove_disconnected_crafting_data(game_data: ParsedGameData) -> None:
    """
    Removes recipes, crafting machines, furnaces, and crafting categories that are disconnected from the retained crafting system.

    A recipe must have at least one category supported by a retained machine.
    A machine must support at least one category used by a retained recipe.
    A crafting category must be referenced by both sides of the relationship.
    """
    recipes = game_data.get("recipes", {})
    crafting_categories = game_data.get("crafting_categories", {})

    machine_collections = (
        game_data.get("crafting_machines", {}),
        game_data.get("furnaces", {}),
    )

    total_removed_recipes = 0
    total_removed_machines = 0
    total_removed_categories = 0

    while True:
        removed_this_pass = 0

        machine_categories = {
            category
            for machines in machine_collections
            for machine in machines.values()
            for category in machine.get("crafting_categories") or []
        }

        removed_recipes = _remove_prototypes(
            recipes,
            lambda recipe: (
                not (set(recipe.get("categories") or []) & machine_categories)  # noqa: B023
            ),
        )

        recipe_categories = {
            category
            for recipe in recipes.values()
            for category in recipe.get("categories") or []
        }

        removed_machines = 0

        for machines in machine_collections:
            removed_machines += _remove_prototypes(
                machines,
                lambda machine: (
                    not (
                        set(machine.get("crafting_categories") or [])
                        & recipe_categories  # noqa: B023
                    )
                ),
            )

        machine_categories = {
            category
            for machines in machine_collections
            for machine in machines.values()
            for category in machine.get("crafting_categories") or []
        }

        connected_categories = recipe_categories & machine_categories

        removed_categories = _remove_prototypes(
            crafting_categories,
            lambda category: category["name"] not in connected_categories,  # noqa: B023
        )

        total_removed_recipes += removed_recipes
        total_removed_machines += removed_machines
        total_removed_categories += removed_categories

        removed_this_pass += removed_recipes + removed_machines + removed_categories

        if removed_this_pass == 0:
            break

    logger.debug(
        "Removed %d disconnected recipes, %d machines, and %d crafting categories",
        total_removed_recipes,
        total_removed_machines,
        total_removed_categories,
    )


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


def _remove_materials_not_used_in_recipes(game_data: ParsedGameData) -> None:
    """
    Remove items and fluids that are not referenced by any remaining recipe.
    """
    used_items: set[str] = set()
    used_fluids: set[str] = set()

    for recipe in game_data.get("recipes", {}).values():
        materials = (recipe.get("ingredients") or []) + (recipe.get("results") or [])

        for material in materials:
            if material.get("type") == "item":
                used_items.add(material["name"])
            elif material.get("type") == "fluid":
                used_fluids.add(material["name"])

    removed_items = _remove_prototypes(
        game_data.get("items", {}),
        lambda item: item["name"] not in used_items,
    )

    removed_fluids = _remove_prototypes(
        game_data.get("fluids", {}),
        lambda fluid: fluid["name"] not in used_fluids,
    )

    logger.debug("Removed %d items unused by recipes", removed_items)
    logger.debug("Removed %d fluids unused by recipes", removed_fluids)


def _remove_redundant_machines(game_data: ParsedGameData) -> None:
    """
    Remove only machines that are explicitly known to be directly superseded for the simulator's purposes.
    """
    redundant = _get_redundant_machines(game_data)
    removed = 0

    for collection_name in ("crafting_machines", "furnaces", "miners"):
        removed += _remove_prototypes(
            game_data.get(collection_name, {}),
            lambda machine: machine["name"] in redundant,
        )

    logger.debug("Removed %d explicitly redundant machines", removed)


def _count_prototypes(game_data: ParsedGameData) -> int:
    """
    Returns the total number of prototypes in the data.
    """

    return sum(len(prototypes) for prototypes in game_data.values())


def normalise_game_data(game_data: ParsedGameData) -> ParsedGameData:
    """
    Apply Factorio defaults and perform only conservative cleanup:

    - normalise missing/default values;
    - remove structurally empty recipes;
    - remove recipes that reference missing items or fluids;
    - remove items and fluids unused by any remaining recipe;
    - remove explicitly superseded machines.
    """
    start_count = _count_prototypes(game_data)
    logger.debug("Found %d prototypes", start_count)

    _apply_factorio_defaults(game_data)
    _normalise_resource_result(game_data)

    _remove_prototype_placeholders(game_data)

    _remove_empty_recipes(game_data)
    _remove_recipes_with_missing_materials(game_data)
    _remove_disconnected_crafting_data(game_data)
    _remove_materials_not_used_in_recipes(game_data)
    _remove_redundant_machines(game_data)

    end_count = _count_prototypes(game_data)

    logger.info(
        "Normalisation complete: %d prototypes removed, %d retained",
        start_count - end_count,
        end_count,
    )

    return game_data
