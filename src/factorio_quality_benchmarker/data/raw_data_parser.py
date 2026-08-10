import json
import shutil
from pathlib import Path

"""
The system requires the recycler and quality mechanics to be present in the data dump to work. 
In version 2.0, the Quality mod is required. In version 2.1, both the Quality and Recycler mods are required.
"""
required_mods = {
    "2.0": {"Quality"},
    "2.1": {"Quality", "Recycler"},
}


# Helper functions for reading and writing JSON files
def _read_json_from_file(file_path: Path, error_message: str) -> dict:
    try:
        with file_path.open("r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(error_message + f" (File path: {file_path})")


def _write_json_to_file(data: dict, parser_output_path: Path, filename: str) -> None:
    output_path = parser_output_path / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(data, f, indent=4)


# Helper functions for the parsing process
def _write_prototype_files(raw_data: dict, parser_output_path: Path) -> None:
    """Parses all the required data from the raw data and writes it to the output files."""

    parse_jobs = {
        "items.json": (
            [
                "item",
                "ammo",
                "armor",
                "capsule",
                "gun",
                "item-with-entity-data",
                "module",
                "rail-planner",
                "repair-tool",
            ],
            ["name", "type"],
        ),
        "fluids.json": (["fluid"], ["name", "type"]),
        "recipes.json": (
            ["recipe"],
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
        ),
        "crafting_machines.json": (
            ["assembling-machine"],
            [
                "name",
                "crafting_categories",
                "crafting_speed",
                "effect_receiver",
                "module_slots",
                "allowed_effects",
                "selection_box",
                "next_upgrade",
                "energy_usage",
            ],
        ),
        "furnaces.json": (
            ["furnace"],
            [
                "name",
                "crafting_categories",
                "crafting_speed",
                "effect_receiver",
                "module_slots",
                "allowed_effects",
                "selection_box",
                "next_upgrade",
                "energy_usage",
            ],
        ),
        "miners.json": (
            ["mining-drill"],
            [
                "name",
                "resource_categories",
                "mining_speed",
                "module_slots",
                "allowed_effects",
                "selection_box",
                "energy_usage",
            ],
        ),
        "modules.json": (["module"], ["name", "category", "tier", "effect"]),
        "qualities.json": (
            ["quality"],
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
        ),
        "beacons.json": (
            ["beacon"],
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
        ),
        "surfaces.json": (["planet", "surface"], ["name", "surface_properties"]),
        "resources.json": (["resource"], ["name", "category", "minable"]),
    }

    for filename, (prototype_types, fields) in parse_jobs.items():
        _write_json_to_file(
            _parse_prototypes(raw_data, prototype_types, fields),
            parser_output_path,
            filename,
        )


def _parse_prototypes(
    raw_data: dict, prototype_types: list[str], fields: list[str]
) -> dict:
    """
    Parses the raw data for the specified prototype types and fields.
    Returns a dictionary containing the parsed data.
    """

    parsed = {}

    for prototype_type in prototype_types:
        prototype_data = raw_data.get(prototype_type, {})
        for name, data in prototype_data.items():
            parsed[name] = {field: data.get(field) for field in fields}

    return parsed


# Validation functions for metadata and raw data
def _validate_metadata_fields(metadata: dict) -> None:
    """
    Validates the metadata dictionary to ensure it contains the required fields. And checks if the required mods for the specified Factorio version are present in the active mods list.
    Raises a ValueError if any required field is missing.
    """

    required_fields = ["factorio_version", "source_file", "active_mods"]

    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"Missing required field in metadata: {field}")

    version = ".".join(metadata["factorio_version"].split(".")[:2])
    active_mods = set(metadata["active_mods"])

    if version not in required_mods:
        raise ValueError(f"Unsupported Factorio version: {version}.")

    required_mods_for_version = required_mods[version]

    missing_mods = required_mods_for_version - active_mods

    if missing_mods:
        raise ValueError(
            f"Missing required mods for Factorio version {version}: {', '.join(missing_mods)}"
        )


def _validate_quality_and_recycler_present(raw_data: dict) -> None:
    """
    Validates that the Quality and Recycler mechanics are present in the raw data.
    Raises a ValueError if either is missing.
    """

    if not raw_data.get("quality"):
        raise ValueError(
            "Quality mechanic is missing from the raw data. Please enable the Quality mod in Factorio before generating the data dump."
        )

    if not raw_data.get("furnace", {}).get("recycler"):
        raise ValueError(
            "Recycler mechanic is missing from the raw data. Please enable the Recycler mod in Factorio before generating the data dump."
        )


def perform_parsing() -> None:
    """
    The entrypoint for the parsing process. Reads the metadata and raw data files, validates the metadata, and then parses the raw data into structured JSON files.
    """

    raw_path = Path("data/raw")
    parser_output_path = Path("data/parsed")

    if parser_output_path.exists():
        shutil.rmtree(parser_output_path)

    parser_output_path.mkdir(parents=True, exist_ok=True)

    metadata = _read_json_from_file(
        raw_path / "metadata.json", "Metadata file not found."
    )

    _validate_metadata_fields(metadata["metadata"])
    _write_json_to_file(metadata, parser_output_path, "metadata.json")

    raw_data = _read_json_from_file(
        raw_path / metadata["metadata"]["source_file"], "Raw data file not found."
    )

    _validate_quality_and_recycler_present(raw_data)

    _write_prototype_files(raw_data, parser_output_path)
