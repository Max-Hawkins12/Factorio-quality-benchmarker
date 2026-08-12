from math import floor

from factorio_quality_benchmarker.model import Beacon


def calculate_maximum_number_of_beacons(
    machine_height: int,
    machine_width: int,
    beacon: Beacon,
) -> int:
    """
    Calculate the maximum number of beacons that can affect a machine.

    Beacons are packed along each side of the machine at the furthest effective distance. The additional four account for the corner positions.
    """
    beacon_height = beacon.height
    beacon_width = beacon.width
    effect_range = beacon.effect_range

    vertical_reach = machine_height + 2 * (effect_range - 1)
    horizontal_reach = machine_width + 2 * (effect_range - 1)

    beacons_on_vertical_sides = 2 * floor(vertical_reach / beacon_height)
    beacons_on_horizontal_sides = 2 * floor(horizontal_reach / beacon_width)

    return beacons_on_vertical_sides + beacons_on_horizontal_sides + 4
