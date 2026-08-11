from .types import ParsedGameData


def has_space_age(data: ParsedGameData) -> bool:
    """Returns whether the Space Age mod was active for the data dump."""
    return "Space Age" in data["metadata"]["metadata"]["active_mods"]
