from .models import AllowedRecipeEffects

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
