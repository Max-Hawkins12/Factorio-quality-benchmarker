import json
from pathlib import Path

raw_path = Path("data/raw/data-raw-dump.json")
parser_output_path = Path("data/parsed")


def read_json_from_file(file_path: Path) -> dict:
    try:
        with file_path.open("r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"There is no factorio data dump at {file_path}. Please import the data dump first."
        )


def write_json_to_file(data: dict, file_name: str) -> None:
    output_path: Path = parser_output_path / file_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(data, f, indent=4)


def parse_all(raw_data: dict) -> None:
    raw_data = read_json_from_file(raw_path)

    write_json_to_file(parse_materials(raw_data), "materials.json")
    write_json_to_file(parse_recipes(raw_data), "recipes.json")
    write_json_to_file(parse_crafting_machines(raw_data), "crafting_machines.json")
    write_json_to_file(parse_miners(raw_data), "miners.json")
    write_json_to_file(parse_modules(raw_data), "modules.json")
    write_json_to_file(parse_qualities(raw_data), "qualities.json")
    write_json_to_file(parse_beacons(raw_data), "beacons.json")


def parse_prototypes(prototypes: dict, fields: list[str]) -> dict:
    parsed = {}

    for name, data in prototypes.items():
        parsed[name] = {field: data.get(field) for field in fields}

    return parsed


def parse_materials(raw_data: dict) -> dict:
    materials = {**raw_data.get("item", {}), **raw_data.get("fluid", {})}

    return parse_prototypes(
        materials,
        [
            "name",
            "type",
        ],
    )


def parse_recipes(raw_data: dict) -> dict:
    recipes = raw_data.get("recipe", {})

    return parse_prototypes(
        recipes,
        [
            "name",
            "categories",
            "ingredients",
            "results",
            "energy_required",
            "allow_productivity",
            "allow_quality",
            "surface_conditions",
        ],
    )


def parse_crafting_machines(raw_data: dict) -> dict:

    crafting_machines = {
        **raw_data.get("assembling-machine", {}),
        **raw_data.get("furnace", {}),
    }

    return parse_prototypes(
        crafting_machines,
        [
            "name",
            "crafting_categories",
            "crafting_speed",
            "effect_receiver",
            "module_slots",
            "allowed_effects",
            "selection_box",
            "energy_usage",
        ],
    )


def parse_miners(raw_data: dict) -> dict:
    miners = raw_data.get("mining-drill", {})

    return parse_prototypes(
        miners,
        [
            "name",
            "resource_categories",
            "mining_speed",
            "module_slots",
            "allowed_effects",
            "selection_box",
            "energy_usage",
        ],
    )


def parse_modules(raw_data: dict) -> dict:
    modules = raw_data.get("module", {})

    return parse_prototypes(
        modules,
        [
            "name",
            "category",
            "tier",
            "effect",
        ],
    )


def parse_beacons(raw_data: dict) -> dict:
    beacons = raw_data.get("beacon", {})

    return parse_prototypes(
        beacons,
        [
            "name",
            "module_slots",
            "distribution_effectivity",
            "distribution_effectivity_bonus_per_quality_level",
            "profile",
            "allowed_effects",
            "selection_box",
            "supply_area_distance",
            "energy_usage",
        ],
    )


def parse_qualities(raw_data: dict) -> dict:
    qualities = raw_data.get("quality", {})

    return parse_prototypes(
        qualities,
        [
            "name",
            "level",
            "order",
            "next",
            "next_probability",
            "chain_probability",
            "beacon_power_usage_multiplier",
            "mining_drill_resource_drain_multiplier",
        ],
    )


def parse_surfaces(raw_data: dict) -> dict:
    surfaces = {**raw_data.get("planet", {}), **raw_data.get("surface", {})}

    return parse_prototypes(
        surfaces,
        [
            "name",
            "surface_properties",
        ],
    )
