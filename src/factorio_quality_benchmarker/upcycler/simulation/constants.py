from factorio_quality_benchmarker.game.models import Module, ModuleCategory, Quality

from .models import ProductivityResearchLevels, Qualified

# A Qualified module to act as a place holder for an empty module slot
EMPTY_MODULE = Qualified(
    Module(
        name="empty",
        tier=0,
        category=ModuleCategory(type="empty"),
        effects={},
    ),
    Quality(
        name="unknown",
        level=-1,
        next=None,
        next_probability=None,
        chain_probability=None,
    ),
)

# Productivity research level presets
NO_RESEARCH = ProductivityResearchLevels(
    processing_unit_level=0,
    low_density_structure_level=0,
    steel_level=0,
    plastic_bar_level=0,
    rocket_fuel_level=0,
)


MAX_WITH_PROD_MODULES = ProductivityResearchLevels(
    # Minimum level to reach the productivity cap with legendary modules
    # Use level 10 for minimum plastic bar and rocket fuel level in a cryogenic plant
    processing_unit_level=13,
    low_density_structure_level=15,
    steel_level=15,
    plastic_bar_level=15,
    rocket_fuel_level=15,
)

MAX_WITHOUT_PROD_MODULES = ProductivityResearchLevels(
    # Minimum level to reach the productivity cap with no modules
    # Use level 30 for minimum plastic bar and rocket fuel level in a cryogenic plant
    processing_unit_level=25,
    low_density_structure_level=25,
    steel_level=25,
    plastic_bar_level=25,
    rocket_fuel_level=25,
)

MAX_LEVEL = ProductivityResearchLevels(
    # Research provides enough productivity to meet the productivity cap
    processing_unit_level=30,
    low_density_structure_level=30,
    steel_level=30,
    plastic_bar_level=30,
    rocket_fuel_level=30,
)

# Items which have a valid recipe and/or recycling recipe, but are uncraftable ingame
"""
NOTE:
INFO: Generating recipe graph index for 307 items from 644 recipes 
INFO: Generated recipe graph index in 2.91s: 744 production graph references, 968 upcycling graph references 

INFO: Generating recipe graph index for 283 items from 613 recipes 
INFO: Generated recipe graph index in 2.86s: 737 production graph references, 927 upcycling graph references
"""
UNCRAFTABLE_ITEMS = frozenset(
    {
        "bottomless-chest",
        "burner-generator",
        "coin",
        "empty-module-slot",
        "electric-energy-interface",
        "electric-energy-interface-equipment",
        "express-loader",
        "fast-loader",
        "heat-interface",
        "infinity-cargo-wagon",
        "infinity-chest",
        "infinity-pipe",
        "lane-splitter",
        "linked-belt",
        "linked-chest",
        "loader",
        "one-way-valve",
        "overflow-valve",
        "proxy-container",
        "science",
        "selection-tool",
        "simple-entity-with-force",
        "simple-entity-with-owner",
        "top-up-valve",
        "turbo-loader",
    }
)
