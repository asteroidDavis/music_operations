import logging
import sys
from logging import StreamHandler, Formatter, Logger
from typing import NoReturn


def setup_logger(logger: Logger) -> NoReturn:
    logger.setLevel(logging.INFO)

    handler = StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
