import pytest
import logzero
import logging


@pytest.fixture(autouse=True)
def setup_logzero(caplog):
    # Set up logzero to use the same handler as caplog
    logger = logzero.logger
    logger.handlers = []  # Remove existing handlers
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG)
    return logger
