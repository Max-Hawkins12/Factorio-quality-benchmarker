import typer

from factorio_quality_benchmarker.data.loader import load_game_data
from factorio_quality_benchmarker.data.parser import perform_parsing
from factorio_quality_benchmarker.logging_config import configure_logging

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
    load_game_data()


def main() -> None:
    configure_logging(verbose=True)

    app()
