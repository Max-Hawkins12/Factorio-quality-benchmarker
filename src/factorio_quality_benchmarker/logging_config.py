import logging


def configure_logging(verbose: bool = True) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
