import typer

from factorio_quality_benchmarker.data.raw_data_parser import perform_parsing

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


def main() -> None:
    app()
