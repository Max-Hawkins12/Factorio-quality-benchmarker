import logging
from collections.abc import Callable, MutableMapping
from collections.abc import Set as AbstractSet

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
            resource["minable"]["results"] = {
                "type": "item",
                "name": resource["minable"]["result"],
                "amount": 1,
            }

    logger.debug("Normalised resource results field")


# Hard coded values to remove redundant data from the model
DESIRED_MODULE_EFFECTS = {
    "productivity",
    "quality",
    "speed",
}

EXCLUDED_CRAFTING_MACHINES = {
    "assembling-machine-1",
    "assembling-machine-2",
    "oil-refinery",
}

EXCLUDED_FURNACES = {
    "stone-furnace",
    "steel-furnace",
}

EXCLUDED_MINERS = {
    "burner-mining-drill",
    "pumpjack",
}

EXCLUDED_RECIPES = {
    "biter-egg",
    "rocket-part",
    "space-platform-starter-pack",
    "space-platform-starter-pack-recycling",
    "blueprint-recycling",
    "blueprint-book-recycling",
    "deconstruction-planner-recycling",
    "upgrade-planner-recycling",
    "selection-tool-recycling",
    "item-unknown-recycling",
}


def _get_excluded_machines(game_data: ParsedGameData):
    """
    Returns the set of machines that should be excluded based on if Space Age is enabled.
    """
    to_exclude = EXCLUDED_CRAFTING_MACHINES | EXCLUDED_FURNACES | EXCLUDED_MINERS

    if has_space_age(game_data):
        to_exclude = to_exclude | {"electric-mining-drill"}

    return to_exclude


# Helper methods
def _remove_prototypes(
    prototypes: PrototypeCollection,
    should_remove: Callable[[Prototype], bool],
) -> int:
    """
    Removes prototypes for which should_remove returns True.
    Returns the number of entries removed.
    """
    removed = 0

    for prototype_name, prototype in list(prototypes.items()):
        if should_remove(prototype):
            del prototypes[prototype_name]

            removed += 1

    return removed


def _retain_mapping_keys[T](
    mapping: MutableMapping[str, T],
    desired_keys: AbstractSet[str],
) -> int:
    """
    Removes entries from a mapping whose keys are not in desired_keys.
    Returns the number of entries removed.
    """
    removed = 0

    for key in list(mapping):
        if key not in desired_keys:
            del mapping[key]
            removed += 1

    return removed


def _retain_list_values(
    values: list[str],
    desired_values: set[str],
) -> int:
    """
    Removes values that are not in desired_values.
    Returns the number of values removed.
    """
    original_length = len(values)

    values[:] = [value for value in values if value in desired_values]

    return original_length - len(values)


# Methods to clean the data
def _clean_prototype_noise(game_data: ParsedGameData) -> None:
    """
    Removes any prototypes that have names like "*-unknown" or "parameter-*".
    """
    removed = 0

    for prototypes in game_data.values():
        removed += _remove_prototypes(
            prototypes,
            lambda prototype: (
                prototype.get("name", "").endswith("-unknown")
                or prototype.get("name", "").startswith("parameter-")
            ),
        )

    logger.debug("Removed %d prototype placeholders", removed)


def _remove_recipes_with_no_item_outputs(game_data: ParsedGameData) -> None:
    """
    Removes recipes that do not produce any items.
    """
    recipes = game_data.get("recipes", {})

    removed = _remove_prototypes(
        recipes,
        lambda recipe: (
            not any(
                result.get("type") == "item" for result in recipe.get("results") or []
            )
        ),
    )

    logger.debug("Removed %d recipes with no item outputs", removed)


def _remove_fluid_resources(game_data: ParsedGameData) -> None:
    """
    Removes resources that are of type basic-fluid.
    """

    resources = game_data.get("resources", {})

    removed = _remove_prototypes(
        resources, lambda resource: resource.get("category") == "basic-fluid"
    )

    logger.debug("Removed %d fluid resources", removed)


def _remove_fluid_only_miners(game_data: ParsedGameData) -> None:
    """
    Removes miners that are for fluid resources.
    """

    miners = game_data.get("miners", {})

    removed = _remove_prototypes(
        miners,
        lambda miner: all(
            category == "basic-fluid"
            for category in miner.get("resource_categories") or []
        ),
    )

    logger.debug("Removed %d fluid-only miners", removed)


def _remove_modules_with_no_desired_effects(game_data: ParsedGameData) -> None:
    """
    Removes modules that do not effect productivity, quality, or speed.
    """

    modules = game_data.get("modules", {})

    removed = _remove_prototypes(
        modules,
        lambda module: not (module.get("effect", {}).keys() & DESIRED_MODULE_EFFECTS),
    )

    logger.debug("Removed %d modules with no useful effects", removed)


def _remove_machines_that_disallow_quality(game_data: ParsedGameData) -> None:
    """
    Removes crafting machines and furnaces which don't support quality.
    """
    removed = 0

    for collection_name in ("crafting_machines", "furnaces"):
        machines = game_data.get(collection_name, {})

        removed += _remove_prototypes(
            machines,
            lambda machine: "quality" not in (machine.get("allowed_effects") or []),
        )

    logger.debug("Removed %d machines that do not support quality", removed)


def _remove_excluded_machines(game_data: ParsedGameData) -> None:
    """
    Removes machines explicitly excluded from the upcycler model.
    """
    removed = 0

    for collection_name in ("crafting_machines", "furnaces", "miners"):
        machines = game_data.get(collection_name, {})

        removed += _remove_prototypes(
            machines,
            lambda machine: machine["name"] in _get_excluded_machines(game_data),
        )

    logger.debug("Removed %d manually excluded machines", removed)


def _remove_excluded_recipes(game_data: ParsedGameData) -> None:
    """
    Removes recipes explicitly excluded from the upcycler model.
    """

    recipes = game_data.get("recipes", {})

    removed = _remove_prototypes(
        recipes,
        lambda recipe: recipe["name"] in EXCLUDED_RECIPES,
    )

    logger.debug("Removed %d manually excluded recipes", removed)


def _remove_materials_not_used_in_recipes(game_data: ParsedGameData) -> None:
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

    removed_items = _remove_prototypes(
        game_data.get("items", {}),
        lambda item: item["name"] not in used_items,
    )

    removed_fluids = _remove_prototypes(
        game_data.get("fluids", {}),
        lambda fluid: fluid["name"] not in used_fluids,
    )

    logger.debug("Removed %d unused items", removed_items)
    logger.debug("Removed %d unused fluids", removed_fluids)


def _remove_undesired_effects(game_data: ParsedGameData) -> None:
    """
    Removes effects that are irrelevant to the optimiser.
    """
    for module in game_data.get("modules", {}).values():
        effects = module.get("effect")

        if isinstance(effects, dict):
            _retain_mapping_keys(
                effects,
                DESIRED_MODULE_EFFECTS,
            )

    for collection_name in ("crafting_machines", "furnaces", "miners", "beacons"):
        for machine in game_data.get(collection_name, {}).values():
            allowed_effects = machine.get("allowed_effects")

            if isinstance(allowed_effects, list):
                _retain_list_values(
                    allowed_effects,
                    DESIRED_MODULE_EFFECTS,
                )

    logger.debug("Removed undesired effects")


def _remove_unused_surface_properties(game_data: ParsedGameData) -> None:
    """
    Removes surface properties that are not referenced by any retained recipe
    surface condition.
    """
    used_properties: set[str] = set()

    for recipe in game_data.get("recipes", {}).values():
        for condition in recipe.get("surface_conditions") or []:
            used_properties.add(condition["property"])

    for surface in game_data.get("surfaces", {}).values():
        properties = surface.get("surface_properties")

        if isinstance(properties, dict):
            _retain_mapping_keys(
                properties,
                used_properties,
            )

    logger.debug("Removed unused surface properties")


def _validate_recipe_machine_coverage(game_data: ParsedGameData) -> None:
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


def _count_prototypes(game_data: ParsedGameData) -> int:
    """
    Returns the total number of prototypes in the data
    """

    total = 0

    for prototype in game_data.values():
        total += len(prototype)

    return total


def normalise_game_data(game_data: ParsedGameData) -> ParsedGameData:
    """
    The entry point to the normaliser. Adds the missing Factorio engine default data, then executes all cleaning steps.
    And verifies that there exists a machine to craft all remaining recipes
    """
    start_count = _count_prototypes(game_data)

    logger.debug("Found %d prototypes", start_count)

    _apply_factorio_defaults(game_data)
    _normalise_resource_result(game_data)

    _clean_prototype_noise(game_data)

    _remove_recipes_with_no_item_outputs(game_data)
    _remove_fluid_resources(game_data)
    _remove_fluid_only_miners(game_data)

    _remove_modules_with_no_desired_effects(game_data)
    _remove_machines_that_disallow_quality(game_data)

    _remove_excluded_machines(game_data)
    _remove_excluded_recipes(game_data)
    _remove_materials_not_used_in_recipes(game_data)

    _remove_undesired_effects(game_data)
    _remove_unused_surface_properties(game_data)

    _validate_recipe_machine_coverage(game_data)

    end_count = _count_prototypes(game_data)

    logger.info(
        "Normalisation complete: %d prototypes removed, %d retained",
        start_count - end_count,
        end_count,
    )

    return game_data
