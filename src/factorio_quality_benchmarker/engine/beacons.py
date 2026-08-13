from math import floor

from factorio_quality_benchmarker.model import Beacon, Crafter, Miner


def calculate_maximum_number_of_beacons(
    machine: Crafter | Miner,
    beacon: Beacon,
) -> int:
    """
    Calculate the maximum number of beacons that can affect a machine.

    Beacons are packed along each side of the machine at the furthest effective distance. The additional four account for the corner positions.
    """
    vertical_reach = machine.height + 2 * (beacon.effect_range - 1)
    horizontal_reach = machine.width + 2 * (beacon.effect_range - 1)

    beacons_on_vertical_sides = 2 * floor(vertical_reach / beacon.height)
    beacons_on_horizontal_sides = 2 * floor(horizontal_reach / beacon.width)

    return beacons_on_vertical_sides + beacons_on_horizontal_sides + 4
