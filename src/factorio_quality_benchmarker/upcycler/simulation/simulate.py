from collections.abc import Mapping

from factorio_quality_benchmarker.game import GameData
from factorio_quality_benchmarker.game.models import Quality

from .models import Named, Qualified, QualifiedIndex, SimulationData


def _apply_quality[T: Named](
    entities: Mapping[str, T],
    qualities: tuple[Quality, ...],
) -> QualifiedIndex[T]:

    return {
        quality: {name: Qualified(entity, quality) for name, entity in entities.items()}
        for quality in qualities
    }


def build_simulation_data(game_data: GameData) -> SimulationData:

    qualities = tuple(game_data.qualities.values())

    return SimulationData(
        game_data=game_data,
        crafters_by_quality=_apply_quality(game_data.crafters, qualities),
        miners_by_quality=_apply_quality(game_data.miners, qualities),
        modules_by_quality=_apply_quality(game_data.modules, qualities),
        beacons_by_quality=_apply_quality(game_data.beacons, qualities),
    )
