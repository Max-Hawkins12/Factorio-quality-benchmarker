from pathlib import Path

import typer

from factorio_quality_benchmarker.data import load_game_data, perform_parsing
from factorio_quality_benchmarker.optimiser import optimise
from factorio_quality_benchmarker.optimiser.simulation import build_simulation_context
from factorio_quality_benchmarker.results import export_results, markdown_table

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

    target = simulation.items["tungsten-plate"]

    print(markdown_table(target, results[simulation.items["tungsten-plate"]][0]))
    print()
    print(markdown_table(target, results[simulation.items["tungsten-plate"]][1]))
    print()
    print(markdown_table(target, results[simulation.items["tungsten-plate"]][-1]))
    print()
    print(
        markdown_table(
            simulation.items["processing-unit"],
            results[simulation.items["processing-unit"]][0],
        )
    )
    print()
    print(
        markdown_table(
            simulation.items["processing-unit"],
            results[simulation.items["processing-unit"]][14],
        )
    )
    print()
    print(
        markdown_table(
            simulation.items["electromagnetic-plant"],
            results[simulation.items["electromagnetic-plant"]][0],
        )
    )

    export_results(results, Path("data/results"))
