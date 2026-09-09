import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.upcycler.simulation import build_simulation_data

app = typer.Typer()


@app.command()
def parse() -> None:
    perform_parsing()


@app.command()
def dev() -> None:
    # Temp command

    game_data = load_game_data()

    simulation_data = build_simulation_data(game_data)
