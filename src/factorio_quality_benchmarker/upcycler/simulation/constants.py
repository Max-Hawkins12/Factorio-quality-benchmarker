from factorio_quality_benchmarker.game.models import Module, ModuleCategory, Quality

from .models import Qualified

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
