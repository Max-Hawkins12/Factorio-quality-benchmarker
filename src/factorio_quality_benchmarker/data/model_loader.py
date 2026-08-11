"""
Notes:

Recycling Recipe Probabilities -> different ways of expressing it

crafting machine -> calculate size -> calculate max beacons

"""

import json
import logging
from collections.abc import Callable
from math import ceil
from os import listdir
from pathlib import Path
from typing import TypeVar

from factorio_quality_benchmarker.engine import calculate_product_ammount
from factorio_quality_benchmarker.model import (
    Beacon,
    CraftingCategory,
    CraftingMachine,
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

T = TypeVar("T")
logger = logging.getLogger(__name__)


def _load_parsed_file(filename: str, parsed_path: Path) -> PrototypeCollection:
    file_path = parsed_path / filename

    with file_path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Expected {filename} to contain a JSON object")

    return data


def _load_all_game_data(parsed_path: Path) -> ParsedGameData:
    all_files = listdir(parsed_path)

    for f in all_files:
        if not f.endswith(".json"):
            raise ValueError(
                f"There is a non-JSON file {f} in {parsed_path}. Please remove it."
            )

    return {
        f.removesuffix(".json"): _load_parsed_file(f, parsed_path) for f in all_files
    }


def _load_collection[T](
    data: ParsedGameData,
    collection_name: str,
    constructor: Callable[[str, Prototype], T],
) -> dict[str, T]:
    json_objects = data.get(collection_name, {})

    return {
        name: constructor(name, prototype) for name, prototype in json_objects.items()
    }


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


def _collect_crafting_categories(data: ParsedGameData) -> dict[str, CraftingCategory]:
    category_names: set[str] = set()

    for recipe in data.get("recipes", {}).values():
        category_names.update(recipe.get("categories", []))

    for machine in data.get("crafting_machines", {}).values():
        category_names.update(machine.get("crafting_categories", []))

    return {name: CraftingCategory(name=name) for name in category_names}


def _collect_module_effects(data: ParsedGameData) -> dict[str, ModuleEffect]:
    effect_names: set[str] = set()

    for module in data.get("modules", {}).values():
        effect_names.update(module.get("effect", []))

    for collection_name in ("crafting_machines", "furnaces", "miners"):
        for machine in data.get(collection_name, {}).values():
            effect_names.update(
                machine.get("allowed_effects", [])
                if machine.get("allowed_effects", []) is not None
                else []
            )

    return {effect: ModuleEffect(effect=effect) for effect in effect_names}


def _collect_resource_categories(data: ParsedGameData) -> dict[str, ResourceCategory]:
    category_names: set[str] = set()

    for resource in data.get("resources", {}).values():
        category_names.add(resource["category"])

    for miner in data.get("miners", {}).values():
        category_names.update(miner.get("resource_categories", []))

    return {name: ResourceCategory(name=name) for name in category_names}


def _collect_surface_properties(data: ParsedGameData) -> dict[str, SurfaceProperty]:
    property_names: set[str] = set()

    for surface in data.get("surfaces", {}).values():
        property_names.update(surface.get("surface_properties", []))

    return {property: SurfaceProperty(property=property) for property in property_names}


def _load_ingredient(
    ingredient: Prototype,
    items: dict[str, Item],
    fluids: dict[str, Fluid],
) -> Ingredient:
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
    selection_box = machine["selection_box"]

    return ceil((selection_box[0][0] * -1) + selection_box[1][0])


def _get_height(machine: Prototype) -> int:
    selection_box = machine["selection_box"]

    return ceil((selection_box[0][1] * -1) + selection_box[1][1])


def _get_inherent_productivity(machine: Prototype) -> float:
    if machine.get("effect_receiver", {}):
        return (
            machine.get("effect_receiver", {})
            .get("base_effect", {})
            .get("productivity", 0.0)
        )

    return 0.0


def _load_crafting_machines(
    data: ParsedGameData,
    crafting_categories: dict[str, CraftingCategory],
    module_effects: dict[str, ModuleEffect],
) -> dict[str, CraftingMachine]:

    def constructor(name: str, machine: Prototype) -> CraftingMachine:
        return CraftingMachine(
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

    machines = _load_collection(data, "crafting_machines", constructor)
    furnaces = _load_collection(data, "furnaces", constructor)

    return machines | furnaces


def _load_miners(
    data: ParsedGameData,
    resource_categories: dict[str, ResourceCategory],
    module_effects: dict[str, ModuleEffect],
) -> dict[str, Miner]:

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


def _simulate_resource_product(resource: Prototype) -> Prototype:
    if "results" in resource:
        return resource["results"]

    return {
        "type": "item",
        "name": resource["result"],
        "amount": 1,
    }


def _load_resources(
    data: ParsedGameData,
    resource_categories: dict[str, ResourceCategory],
    items: dict[str, Item],
    fluids: dict[str, Fluid],
) -> dict[str, Resource]:

    def constructor(name: str, resource: Prototype) -> Resource:
        return Resource(
            name=name,
            category=resource_categories[resource["category"]],
            mining_time=resource["minable"]["mining_time"],
            product=_load_product(
                _simulate_resource_product(resource["minable"]), items, fluids
            ),
        )

    return _load_collection(data, "resources", constructor)


def _load_surfaces(
    data: ParsedGameData,
    surface_properties: dict[str, SurfaceProperty],
) -> dict[str, Surface]:

    def constructor(name: str, surface: Prototype) -> Surface:
        return Surface(
            name=name,
            properties={
                surface_properties[property_name]: value
                for property_name, value in surface["surface_properties"].items()
            },
        )

    return _load_collection(data, "surfaces", constructor)


def _load_qualities(data: ParsedGameData) -> dict[str, Quality]:
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

    return qualities


def _load_version(data: ParsedGameData) -> str:
    return data["metadata"]["metadata"]["factorio_version"]


def _has_space_age(data: ParsedGameData) -> bool:
    return "Space Age" in data["metadata"]["metadata"]["active_mods"]


def load_game_data() -> GameData:
    parsed_path = Path("data/parsed")

    logger.info("Loading parsed data...")
    raw_data = _load_all_game_data(parsed_path)

    logger.info("Normalising parsed data...")
    data = normalise_game_data(raw_data)

    crafting_categories = _collect_crafting_categories(data)
    module_effects = _collect_module_effects(data)
    resource_categories = _collect_resource_categories(data)
    surface_properties = _collect_surface_properties(data)

    items = _load_items(data)
    fluids = _load_fluids(data)

    return GameData(
        items=items,
        fluids=fluids,
        recipes=_load_recipes(
            data,
            items,
            fluids,
            crafting_categories,
            surface_properties,
        ),
        crafting_machines=_load_crafting_machines(
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
        has_space_age=_has_space_age(data),
    )
