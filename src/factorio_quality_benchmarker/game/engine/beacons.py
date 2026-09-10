from math import floor

from factorio_quality_benchmarker.game.models import Beacon, Machine
from factorio_quality_benchmarker.upcycler.simulation import Qualified

from .quality import get_qualified_beacon_distribution_effectivity


def calculate_maximum_beacons(machine: Machine, beacon: Beacon) -> int:
    """
    Geometrically calculate the maximum number of beacons that can affect a machine.

    Beacons are packed along each side of the machine at the furthest effective distance. The additional four account for the corner positions.
    """
    vertical_reach = machine.height + 2 * (beacon.effect_range - 1)
    horizontal_reach = machine.width + 2 * (beacon.effect_range - 1)

    beacons_on_vertical_sides = 2 * floor(vertical_reach / beacon.height)
    beacons_on_horizontal_sides = 2 * floor(horizontal_reach / beacon.width)

    return beacons_on_vertical_sides + beacons_on_horizontal_sides + 4


def calculate_distribution_effectivity(
    beacon: Qualified[Beacon],
    num_beacons: int,
) -> float:
    """
    Use the beacon's deminishing returns profile and Factorio engine rules to calculate the distribution effectivity for the number of beacons and quality level.
    """
    return (
        get_qualified_beacon_distribution_effectivity(beacon)
        * num_beacons
        * beacon.entity.diminishing_returns_profile[num_beacons - 1]
        if num_beacons > 0
        else 0.0
    )
