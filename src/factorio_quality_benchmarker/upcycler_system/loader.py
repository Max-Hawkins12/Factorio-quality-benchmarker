import json
from pathlib import Path

from .models import UpcyclerSystem
from .serialsation import serialise_upcycler_system


def write_upcycler_system(
    system: UpcyclerSystem,
    directory: Path,
) -> None:

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = directory / f"{system.target.name}.json"

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            serialise_upcycler_system(system),
            file,
            indent=2,
        )


def write_upcycler_systems(
    systems: tuple[UpcyclerSystem, ...],
    directory: Path,
) -> None:
    for system in systems:
        write_upcycler_system(system, directory)


def _load_file(
    filename: str,
    directory: Path,
) -> dict:
    file_path = directory / (filename + ".json")

    with file_path.open("r") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Expected {filename} to contain a JSON object")

    return data
    


def load_upcycler_system(
    filename: str,
    directory: Path,
) -> UpcyclerSystem:

