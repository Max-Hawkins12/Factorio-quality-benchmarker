from factorio_quality_benchmarker.game.models import Module, ModuleCategory, Quality
from factorio_quality_benchmarker.optimiser.simulation import Qualified

from .models import AllowedRecipeEffects

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

NO_EFFECTS = AllowedRecipeEffects(productivity=False, quality=False)
PRODUCTIVITY = AllowedRecipeEffects(productivity=True, quality=False)
QUALITY = AllowedRecipeEffects(productivity=False, quality=True)
PRODUCTIVITY_AND_QUALITY = AllowedRecipeEffects(productivity=True, quality=True)

ALL_RECIPE_EFFECTS = (
    NO_EFFECTS,
    PRODUCTIVITY,
    QUALITY,
    PRODUCTIVITY_AND_QUALITY,
)
