"""Shared logging setup for music-operations."""

import logging
import sys
from logging import Formatter, Logger, StreamHandler


def setup_logger(logger: Logger) -> None:
    """Configure *logger* with a stdout handler and standard format.

    Args:
        logger: The :class:`logging.Logger` instance to configure.
    """
    logger.setLevel(logging.INFO)

    handler = StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
