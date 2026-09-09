from factorio_quality_benchmarker.app import app, configure_logging


def main():
    configure_logging(verbose=False)

    app()
