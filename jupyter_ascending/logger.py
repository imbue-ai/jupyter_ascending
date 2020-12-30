import os
import sys
import tempfile

from loguru import logger

from jupyter_ascending._environment import LOG_LEVEL
from jupyter_ascending._environment import SHOW_TO_STDOUT
from jupyter_ascending._environment import IS_LOGGING_ENABLED

__all__ = ["J_LOGGER"]

config = {
    "handlers": [{"sink": os.path.join(tempfile.gettempdir(), "jupyter_ascending", "log.log"), "serialize": False, "level": LOG_LEVEL}],
}

if SHOW_TO_STDOUT:
    config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": LOG_LEVEL})
else:
    config["handlers"].append({"sink": sys.stdout, "format": "{time} - {message}", "level": "WARNING"})

logger.configure(**config)  # type: ignore

if not IS_LOGGING_ENABLED:
    # don't want any of this logging config to interfere with user applications
    logger.disable("jupyter_ascending")

    # but we do need to ensure that warnings, etc are shown:
    old_warning_function = logger.warning
    def new_warning(message, *args, **kwargs):
        old_warning_function(message, *args, **kwargs)
        print(message.format(*args, **kwargs))
    logger.warning = new_warning

    old_error_function = logger.error
    def new_error(message, *args, **kwargs):
        old_error_function(message, *args, **kwargs)
        print(message.format(*args, **kwargs))
    logger.error = new_error

    old_critical_function = logger.critical
    def new_critical(message, *args, **kwargs):
        old_critical_function(message, *args, **kwargs)
        print(message.format(*args, **kwargs))
    logger.critical = new_critical

# Just give a global constant to import for now
J_LOGGER = logger
