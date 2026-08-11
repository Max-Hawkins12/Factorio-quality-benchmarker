import json
import logging
from collections.abc import Callable
from math import ceil
from pathlib import Path

from factorio_quality_benchmarker.engine import calculate_product_ammount
from factorio_quality_benchmarker.model import (
    Beacon,
    Crafter,
    CraftingCategory,
    Fluid,
    FluidIngredient,
    FluidProduct,
    GameData,
    Ingredient,
    Item,
    ItemIngredient,
    ItemProduct,
    Miner,
    Module,
    ModuleEffect,
    Product,
    Quality,
    Recipe,
    Resource,
    ResourceCategory,
    Surface,
    SurfaceCondition,
    SurfaceProperty,
)

from .normaliser import normalise_game_data
from .types import ParsedGameData, Prototype, PrototypeCollection
from .utils import has_space_age

logger = logging.getLogger(__name__)


def _load_parsed_file(
    filename: str,
    parsed_path: Path,
) -> PrototypeCollection:
    """Loads one parsed JSON prototype collection."""
    file_path = parsed_path / filename

    logger.debug("Loading parsed file: %s", file_path)

    with file_path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Expected {filename} to contain a JSON object")

    logger.debug(
        "Loaded %s containing %d entries",
        filename,
        len(data),
    )

    return data


def _load_all_game_data(parsed_path: Path) -> ParsedGameData:
    """Loads all parsed JSON files into the intermediate data representation."""
    files = sorted(parsed_path.iterdir())

    for file_path in files:
        if not file_path.is_file() or file_path.suffix != ".json":
            raise ValueError(
                f"There is a non-JSON file {file_path.name} in {parsed_path}. "
                "Please remove it."
            )

    logger.debug(
        "Found %d parsed JSON files in %s",
        len(files),
        parsed_path,
    )

    return {
        file_path.stem: _load_parsed_file(file_path.name, parsed_path)
        for file_path in files
    }


def _load_collection[T](
    data: ParsedGameData,
    collection_name: str,
    constructor: Callable[[str, Prototype], T],
) -> dict[str, T]:
    """Constructs a model collection from one parsed prototype collection."""
    prototypes = data.get(collection_name, {})

    objects = {
        name: constructor(name, prototype) for name, prototype in prototypes.items()
    }

    logger.debug(
        "Loaded %d %s",
        len(objects),
        collection_name.replace("_", " "),
    )

    return objects


def _collect_crafting_categories(
    data: ParsedGameData,
) -> dict[str, CraftingCategory]:
    """Collects canonical crafting-category objects from their references."""
    category_names: set[str] = set()

    for recipe in data.get("recipes", {}).values():
        category_names.update(recipe.get("categories") or [])

    for collection_name in ("crafting_machines", "furnaces"):
        for machine in data.get(collection_name, {}).values():
            category_names.update(machine.get("crafting_categories") or [])

    categories = {name: CraftingCategory(name=name) for name in category_names}

    logger.debug(
        "Collected %d crafting categories",
        len(categories),
    )

    return categories


def _collect_module_effects(
    data: ParsedGameData,
) -> dict[str, ModuleEffect]:
    """Collects canonical module-effect objects from their references."""
    effect_names: set[str] = set()

    # A module effect is stored as a mapping from effect name to magnitude.
    for module in data.get("modules", {}).values():
        effect_names.update(module.get("effect") or {})

    for collection_name in ("crafting_machines", "furnaces", "miners"):
        for machine in data.get(collection_name, {}).values():
            effect_names.update(machine.get("allowed_effects") or [])

    effects = {effect: ModuleEffect(effect=effect) for effect in effect_names}

    logger.debug(
        "Collected %d module effects",
        len(effects),
    )

    return effects


def _collect_resource_categories(
    data: ParsedGameData,
) -> dict[str, ResourceCategory]:
    """Collects canonical resource-category objects from resources and miners."""
    category_names: set[str] = set()

    for resource in data.get("resources", {}).values():
        category_names.add(resource["category"])

    for miner in data.get("miners", {}).values():
        category_names.update(miner.get("resource_categories") or [])

    categories = {name: ResourceCategory(name=name) for name in category_names}

    logger.debug(
        "Collected %d resource categories",
        len(categories),
    )

    return categories


def _collect_surface_properties(
    data: ParsedGameData,
) -> dict[str, SurfaceProperty]:
    """Collects canonical surface-property objects from values and constraints."""
    property_names: set[str] = set()

    for surface in data.get("surfaces", {}).values():
        property_names.update((surface.get("surface_properties") or {}).keys())

    for recipe in data.get("recipes", {}).values():
        for condition in recipe.get("surface_conditions") or []:
            property_names.add(condition["property"])

    properties = {name: SurfaceProperty(property=name) for name in property_names}

    logger.debug(
        "Collected %d surface properties",
        len(properties),
    )

    return properties


def _load_items(data: ParsedGameData) -> dict[str, Item]:
    return _load_collection(
        data,
        "items",
        lambda name, _: Item(name=name),
    )


def _load_fluids(data: ParsedGameData) -> dict[str, Fluid]:
    return _load_collection(
        data,
        "fluids",
        lambda name, _: Fluid(name=name),
    )


def _load_ingredient(
    ingredient: Prototype,
    items: dict[str, Item],
    fluids: dict[str, Fluid],
) -> Ingredient:
    """Resolves an ingredient's material name to its canonical model object."""
    name = ingredient["name"]
    amount = ingredient["amount"]

    match ingredient["type"]:
        case "item":
            return ItemIngredient(
                item=items[name],
                amount=amount,
            )

        case "fluid":
            return FluidIngredient(
                fluid=fluids[name],
                amount=amount,
            )

        case ingredient_type:
            raise ValueError(f"Unknown ingredient type: {ingredient_type!r}")


def _load_product(
    product: Prototype,
    items: dict[str, Item],
    fluids: dict[str, Fluid],
) -> Product:
    """
    Resolves a product's material and converts its dump representation to its
    expected output amount.
    """
    name = product["name"]
    amount = calculate_product_ammount(product)

    match product["type"]:
        case "item":
            return ItemProduct(
                item=items[name],
                amount=amount,
            )

        case "fluid":
            return FluidProduct(
                fluid=fluids[name],
                amount=amount,
            )

        case product_type:
            raise ValueError(f"Unknown product type: {product_type!r}")


def _load_recipes(
    data: ParsedGameData,
    items: dict[str, Item],
    fluids: dict[str, Fluid],
    crafting_categories: dict[str, CraftingCategory],
    surface_properties: dict[str, SurfaceProperty],
) -> dict[str, Recipe]:
    """Loads recipes and resolves all material, category, and surface references."""

    def constructor(name: str, recipe: Prototype) -> Recipe:
        return Recipe(
            name=name,
            categories=frozenset(
                crafting_categories[category] for category in recipe["categories"]
            ),
            ingredients=tuple(
                _load_ingredient(ingredient, items, fluids)
                for ingredient in recipe["ingredients"]
            ),
            # Factorio's dump calls these "results"; the domain model uses
            # Factorio's gameplay terminology, "products".
            products=tuple(
                _load_product(product, items, fluids) for product in recipe["results"]
            ),
            energy_required=recipe["energy_required"],
            allow_productivity=recipe["allow_productivity"],
            allow_quality=recipe["allow_quality"],
            surface_conditions=tuple(
                SurfaceCondition(
                    property=surface_properties[condition["property"]],
                    minimum=condition.get("min"),
                    maximum=condition.get("max"),
                )
                for condition in recipe.get("surface_conditions") or []
            ),
        )

    return _load_collection(data, "recipes", constructor)


def _get_width(machine: Prototype) -> int:
    """Returns the prototype width in tiles from its selection box."""
    selection_box = machine["selection_box"]

    return ceil(selection_box[1][0] - selection_box[0][0])


def _get_height(machine: Prototype) -> int:
    """Returns the prototype height in tiles from its selection box."""
    selection_box = machine["selection_box"]

    return ceil(selection_box[1][1] - selection_box[0][1])


def _get_inherent_productivity(machine: Prototype) -> float:
    """Returns a machine's base productivity bonus, or zero if absent."""
    effect_receiver = machine.get("effect_receiver") or {}
    base_effect = effect_receiver.get("base_effect") or {}

    return base_effect.get("productivity", 0.0)


def _load_crafters(
    data: ParsedGameData,
    crafting_categories: dict[str, CraftingCategory],
    module_effects: dict[str, ModuleEffect],
) -> dict[str, Crafter]:
    """Loads crafting machines and furnaces into one domain collection."""

    def constructor(
        name: str,
        machine: Prototype,
    ) -> Crafter:
        return Crafter(
            name=name,
            categories=frozenset(
                crafting_categories[category]
                for category in machine["crafting_categories"]
            ),
            crafting_speed=machine["crafting_speed"],
            module_slots=machine["module_slots"],
            allowed_effects=frozenset(
                module_effects[effect] for effect in machine["allowed_effects"]
            ),
            inherent_productivity=_get_inherent_productivity(machine),
            width=_get_width(machine),
            height=_get_height(machine),
        )

    machines = _load_collection(
        data,
        "crafting_machines",
        constructor,
    )
    furnaces = _load_collection(
        data,
        "furnaces",
        constructor,
    )

    combined = machines | furnaces

    logger.debug(
        "Combined %d crafting machines and %d furnaces into %d crafters",
        len(machines),
        len(furnaces),
        len(combined),
    )

    return combined


def _load_miners(
    data: ParsedGameData,
    resource_categories: dict[str, ResourceCategory],
    module_effects: dict[str, ModuleEffect],
) -> dict[str, Miner]:
    """Loads miners and resolves their categories and allowed effects."""

    def constructor(name: str, miner: Prototype) -> Miner:
        return Miner(
            name=name,
            resource_categories=frozenset(
                resource_categories[category]
                for category in miner["resource_categories"]
            ),
            mining_speed=miner["mining_speed"],
            module_slots=miner["module_slots"],
            allowed_effects=frozenset(
                module_effects[effect] for effect in miner["allowed_effects"]
            ),
            width=_get_width(miner),
            height=_get_height(miner),
        )

    return _load_collection(data, "miners", constructor)


def _load_beacons(
    data: ParsedGameData,
    module_effects: dict[str, ModuleEffect],
) -> dict[str, Beacon]:
    """Loads beacon prototypes and resolves their supported effects."""

    def constructor(name: str, beacon: Prototype) -> Beacon:
        return Beacon(
            name=name,
            distribution_effectivity=beacon["distribution_effectivity"],
            diminishing_returns_profile=tuple(beacon["profile"]),
            module_slots=beacon["module_slots"],
            allowed_effects=frozenset(
                module_effects[effect] for effect in beacon["allowed_effects"]
            ),
            effect_range=beacon["supply_area_distance"],
            width=_get_width(beacon),
            height=_get_height(beacon),
        )

    return _load_collection(data, "beacons", constructor)


def _load_modules(
    data: ParsedGameData,
    module_effects: dict[str, ModuleEffect],
) -> dict[str, Module]:
    """Loads modules and resolves their effect names to canonical objects."""

    def constructor(name: str, module: Prototype) -> Module:
        return Module(
            name=name,
            tier=module["tier"],
            effects={
                module_effects[effect_name]: amount
                for effect_name, amount in module["effect"].items()
            },
        )

    return _load_collection(data, "modules", constructor)


def _load_resources(
    data: ParsedGameData,
    resource_categories: dict[str, ResourceCategory],
    items: dict[str, Item],
    fluids: dict[str, Fluid],
) -> dict[str, Resource]:
    """Loads mineable resources and resolves their category and product."""

    def constructor(name: str, resource: Prototype) -> Resource:
        minable = resource["minable"]

        return Resource(
            name=name,
            category=resource_categories[resource["category"]],
            mining_time=minable["mining_time"],
            product=_load_product(
                minable["results"],
                items,
                fluids,
            ),
        )

    return _load_collection(data, "resources", constructor)


def _load_surfaces(
    data: ParsedGameData,
    surface_properties: dict[str, SurfaceProperty],
) -> dict[str, Surface]:
    """Loads surfaces using the canonical SurfaceProperty objects."""

    def constructor(name: str, surface: Prototype) -> Surface:
        return Surface(
            name=name,
            properties={
                surface_properties[property_name]: value
                for property_name, value in surface["surface_properties"].items()
            },
        )

    return _load_collection(data, "surfaces", constructor)


def _load_qualities(
    data: ParsedGameData,
) -> dict[str, Quality]:
    """
    Loads qualities recursively so each Quality can directly reference the next
    Quality object despite the models being immutable.
    """
    json_qualities = data.get("qualities", {})
    qualities: dict[str, Quality] = {}

    loading: set[str] = set()

    def load_quality(name: str) -> Quality:
        if name in qualities:
            return qualities[name]

        if name in loading:
            raise ValueError(f"Circular quality reference involving {name!r}")

        try:
            json_quality = json_qualities[name]
        except KeyError:
            raise ValueError(f"Unknown quality referenced: {name!r}") from None

        loading.add(name)

        next_name = json_quality.get("next")
        next_quality = load_quality(next_name) if next_name is not None else None

        quality = Quality(
            name=name,
            level=json_quality["level"],
            next=next_quality,
            next_probability=json_quality.get("next_probability"),
            chain_probability=json_quality.get("chain_probability"),
        )

        qualities[name] = quality
        loading.remove(name)

        return quality

    for quality_name in json_qualities:
        load_quality(quality_name)

    logger.debug(
        "Loaded %d qualities",
        len(qualities),
    )

    return qualities


def _load_version(data: ParsedGameData) -> str:
    """Returns the Factorio version associated with the parsed data."""
    return data["metadata"]["metadata"]["factorio_version"]


def load_game_data() -> GameData:
    """Loads, normalises, and constructs the complete Factorio domain model."""
    parsed_path = Path("data/parsed")

    logger.info("Loading parsed Factorio data from %s", parsed_path)
    raw_data = _load_all_game_data(parsed_path)

    logger.info("Normalising parsed Factorio data")
    data = normalise_game_data(raw_data)

    logger.debug("Collecting shared reference objects")

    crafting_categories = _collect_crafting_categories(data)
    module_effects = _collect_module_effects(data)
    resource_categories = _collect_resource_categories(data)
    surface_properties = _collect_surface_properties(data)

    logger.debug("Loading material objects")

    items = _load_items(data)
    fluids = _load_fluids(data)

    logger.debug("Constructing game model")

    game_data = GameData(
        items=items,
        fluids=fluids,
        recipes=_load_recipes(
            data,
            items,
            fluids,
            crafting_categories,
            surface_properties,
        ),
        crafters=_load_crafters(
            data,
            crafting_categories,
            module_effects,
        ),
        miners=_load_miners(
            data,
            resource_categories,
            module_effects,
        ),
        beacons=_load_beacons(
            data,
            module_effects,
        ),
        modules=_load_modules(
            data,
            module_effects,
        ),
        resources=_load_resources(
            data,
            resource_categories,
            items,
            fluids,
        ),
        surfaces=_load_surfaces(
            data,
            surface_properties,
        ),
        qualities=_load_qualities(data),
        factorio_version=_load_version(data),
        has_space_age=has_space_age(data),
    )

    logger.info(
        "Game data loaded successfully: "
        "%d items, %d fluids, %d recipes, %d crafters, "
        "%d miners, %d resources, %d modules, %d beacons, "
        "%d surfaces, %d qualities",
        len(game_data.items),
        len(game_data.fluids),
        len(game_data.recipes),
        len(game_data.crafters),
        len(game_data.miners),
        len(game_data.resources),
        len(game_data.modules),
        len(game_data.beacons),
        len(game_data.surfaces),
        len(game_data.qualities),
    )

    return game_data
