import sys

from loguru import logger

from jupyter_ascending._environment import LOG_LEVEL
from jupyter_ascending._environment import SHOW_TO_STDOUT

__all__ = ["J_LOGGER"]

config = {
    "handlers": [{"sink": "/tmp/jupyter_ascending/log.log", "serialize": False, "level": LOG_LEVEL}],
}


if SHOW_TO_STDOUT:
    config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": LOG_LEVEL})
else:
    config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": "WARNING"})

logger.configure(**config)  # type: ignore

# Just give a global constant to import for now
J_LOGGER = logger
