import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.optimiser import optimise
from factorio_quality_benchmarker.optimiser.simulation import build_simulation_context

app = typer.Typer()


@app.command()
def parse() -> None:
    perform_parsing()


@app.command()
def run() -> None:
    simulation = build_simulation_context(game_data=load_game_data())

    demo_items = (
        simulation.items["tungsten-plate"],
        simulation.items["processing-unit"],
        simulation.items["electromagnetic-plant"],
    )

    results = optimise(simulation, demo_items)
