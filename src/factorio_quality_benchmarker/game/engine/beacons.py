from math import floor

from factorio_quality_benchmarker.game.models import Beacon, ModuleMachine


def calculate_maximum_beacons(machine: ModuleMachine, beacon: Beacon) -> int:
    """
    Geometrically calculate the maximum number of beacons that can affect a machine.

    Beacons are packed along each side of the machine at the furthest effective distance. The additional four account for the corner positions.
    """
    vertical_reach = machine.height + 2 * (beacon.effect_range - 1)
    horizontal_reach = machine.width + 2 * (beacon.effect_range - 1)

    beacons_on_vertical_sides = 2 * floor(vertical_reach / beacon.height)
    beacons_on_horizontal_sides = 2 * floor(horizontal_reach / beacon.width)

    return beacons_on_vertical_sides + beacons_on_horizontal_sides + 4


def calculate_distribution_effectivity(beacon: Beacon, num_beacons: int) -> float:
    """
    Use the beacon's deminishing returns profile and Factorio engine rules to calculate the distribution effectivity for the number of beacons,
    """
    return (
        beacon.distribution_effectivity
        * num_beacons
        * beacon.diminishing_returns_profile[num_beacons - 1]
        if num_beacons > 0
        else 0.0
    )
