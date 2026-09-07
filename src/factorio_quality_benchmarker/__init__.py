import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.logging_config import configure_logging
from factorio_quality_benchmarker.upcycler.graphs import generate_recipe_graph_index

app = typer.Typer()


@app.command()
def parse() -> None:
    """
    Parses the raw data and generates the output files.
    """
    perform_parsing()


@app.command()
def dev() -> None:
    # Temp command name while the project is still taking shape

    game_data = load_game_data()

    # generate_recipe_graph_index(game_data.materials, game_data.recipes)


def main() -> None:
    configure_logging(verbose=False)

    app()
