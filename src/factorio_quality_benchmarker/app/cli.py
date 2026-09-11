import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.upcycler.graphs import generate_recipe_graph_index
from factorio_quality_benchmarker.upcycler.simulation import (
    NO_RESEARCH,
    RunConfig,
    UpcyclerScope,
    build_simulation_context,
)

app = typer.Typer()


@app.command()
def parse() -> None:
    perform_parsing()


@app.command()
def dev() -> None:
    # Temp command

    game_data = load_game_data()

    simulation = build_simulation_context(
        game_data,
        RunConfig(
            productivity_levels=NO_RESEARCH,
            upcycler_scope=UpcyclerScope.CURATED,
            entity_quality=game_data.qualities["legendary"],
            desired_quality=game_data.qualities["legendary"],
        ),
    )

    generate_recipe_graph_index(
        materials=dict(simulation.materials), recipes=dict(simulation.recipes)
    )
