import typer

from factorio_quality_benchmarker.data.loader import (
    load_game_data,
    load_upcycler_systems,
)
from factorio_quality_benchmarker.data.parser import perform_parsing
from factorio_quality_benchmarker.logging_config import configure_logging
from factorio_quality_benchmarker.model import (
    QualifiedBeacon,
    QualifiedCrafter,
    QualifiedModule,
)

app = typer.Typer()


@app.command()
def parse() -> None:
    """
    Parses the raw data and generates the output files.
    """
    perform_parsing()


@app.command()
def version() -> None:
    """Temp since Typer doesn't like only one command"""
    print("0.1.0")


@app.command()
def dev() -> None:
    # game_data = load_game_data()

    load_upcycler_systems()


def main() -> None:
    configure_logging(verbose=False)

    app()
