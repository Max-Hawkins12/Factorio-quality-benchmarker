import typer

from factorio_quality_benchmarker.data.loader import load_game_data
from factorio_quality_benchmarker.data.parser import perform_parsing
from factorio_quality_benchmarker.logging_config import configure_logging
from factorio_quality_benchmarker.recipe_graph import generate_upcycler_index

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

    upcycler_index = generate_upcycler_index(game_data.materials, game_data.recipes)


def main() -> None:
    configure_logging(verbose=True)

    app()
