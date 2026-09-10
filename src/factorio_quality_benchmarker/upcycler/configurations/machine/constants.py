from .models import RecipeEffects

DESIRED_MODULE_EFFECTS = ("productivity", "quality", "speed")

NO_EFFECTS = RecipeEffects(productivity=False, quality=False)
PRODUCTIVITY = RecipeEffects(productivity=True, quality=False)
QUALITY = RecipeEffects(productivity=False, quality=True)
PRODUCTIVITY_AND_QUALITY = RecipeEffects(productivity=True, quality=True)

ALL_RECIPE_EFFECTS = (
    NO_EFFECTS,
    PRODUCTIVITY,
    QUALITY,
    PRODUCTIVITY_AND_QUALITY,
)
