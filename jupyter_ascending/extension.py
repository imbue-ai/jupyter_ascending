import time

from loguru import logger

import jupyter_ascending.handlers.server_extension
from jupyter_ascending._environment import SYNC_EXTENSION
from jupyter_ascending.handlers import jupyter_notebook
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.utils import get_name_from_python


@logger.catch
def load_ipython_extension(ipython):
    """This is the specially named function that Jupyter will call to load a notebook extension."""
    set_everything_up()


def set_everything_up():
    # Note that this is also called from javascript after a kernel restart

    logger.info("Loading Ipython...")
    setup_logger()

    # Start the server if it's the right name.
    notebook_name = get_name_from_python()
    logger.info("IPYTHON: Loading {notebook}", notebook=notebook_name)

    if f".{SYNC_EXTENSION}.ipynb" not in notebook_name:
        logger.info("IPYTHON: Not loading {notebook} because name does not match", notebook=notebook_name)
        return

    logger.info("IPYTHON LOAD: " + time.ctime() + ": " + notebook_name)
    jupyter_notebook.start_notebook_server_in_thread(notebook_name)


def load_jupyter_server_extension(ipython):
    """This is the specially named function that Jupyter will call to load a server extension."""
    setup_logger()
    ipython.log.info("LOADING JUPYTER ASCENDING SERVER PLUGIN")
    logger.info("SERVER LOAD: " + time.ctime())

    jupyter_ascending.handlers.server_extension.load_extension(ipython)
