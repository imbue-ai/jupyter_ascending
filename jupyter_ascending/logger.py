import os
import sys
import tempfile

from loguru import logger

from jupyter_ascending._environment import LOG_LEVEL
from jupyter_ascending._environment import SHOW_TO_STDOUT


def setup_logger():
    log_file = os.path.join(tempfile.gettempdir(), "jupyter_ascending", "log.log")
    print(f"Logging Jupyter Ascending logs to {log_file}")

    config = {
        "handlers": [{"sink": log_file, "serialize": False, "level": LOG_LEVEL}],
    }

    if SHOW_TO_STDOUT:
        config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": LOG_LEVEL})
    else:
        # Always display warning-and-up output
        config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": "WARNING"})

    logger.configure(**config)  # type: ignore
