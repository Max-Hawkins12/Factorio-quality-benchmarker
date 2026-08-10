"""
Notes:

Recycling Recipe Probabilities -> different ways of expressing it

Nauvis planet settings
    pressure = 1000
    gravity = 10

crafting machine -> calculate size -> calculate max beacons

"""

import json
import logging
from dataclasses import dataclass
from os import listdir
from pathlib import Path
from typing import Any

from factorio_quality_benchmarker.data import normalise_game_data
from factorio_quality_benchmarker.model import (
    Beacon,
    CraftingMachine,
    Fluid,
    Item,
    Miner,
    Module,
    Quality,
    Recipe,
    Surface,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GameData:
    items: dict[str, Item]
    fluids: dict[str, Fluid]

    recipes: dict[str, Recipe]
    crafting_machines: dict[str, CraftingMachine]
    miners: dict[str, Miner]

    modules: dict[str, Module]
    beacons: dict[str, Beacon]

    qualities: dict[str, Quality]
    surfaces: dict[str, Surface]

    factorio_version: str


def _load_parsed_file(filename: str, parsed_path: Path) -> dict:
    file_path = parsed_path / filename

    with file_path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Expected {filename} to contain a JSON object")

    return data


def _load_all_game_data(parsed_path: Path) -> dict[str, Any]:
    all_files = listdir(parsed_path)

    for f in all_files:
        if not f.endswith(".json"):
            raise ValueError(
                f"There is a non-JSON file {f} in {parsed_path}. Please remove it."
            )

    return {
        f.removesuffix(".json"): _load_parsed_file(f, parsed_path) for f in all_files
    }


def load_game_data():
    parsed_path = Path("data/parsed")

    logger.info("Loading parsed data...")
    normalise_game_data(_load_all_game_data(parsed_path))
