import signal
import time

from jupyter_ascending._environment import SYNC_EXTENSION
from jupyter_ascending.handlers import jupyter_notebook
from jupyter_ascending.handlers import jupyter_server
from jupyter_ascending.logger import J_LOGGER
from jupyter_ascending.utils import get_name_from_python


@J_LOGGER.catch
def load_ipython_extension(ipython):
    set_everything_up()


def set_everything_up():
    # Note that this is also called from javascript after a kernel restart

    J_LOGGER.info("Loading Ipython...")

    # Start the server if it's the right name.
    notebook_name = get_name_from_python()
    J_LOGGER.info("IPYTHON: Loading {notebook}", notebook=notebook_name)

    if f".{SYNC_EXTENSION}.ipynb" not in notebook_name:
        J_LOGGER.info("IPYTHON: Note loading {notebook} because name does not match", notebook=notebook_name)
        return

    J_LOGGER.info("IPYTHON LOAD: " + time.ctime() + ": " + notebook_name)
    jupyter_notebook.start_notebook_server_in_thread(notebook_name, jupyter_server)


def load_jupyter_server_extension(ipython):
    ipython.log.info("LOADING SERVER")
    J_LOGGER.info("SERVER LOAD: " + time.ctime())

    server = jupyter_server.start_server_in_thread()
    if not server:
        return

    # HACK:
    # A bit of a hack to make sure the server gets shutdown when we're done here.
    #   Had some problems with hanging servers
    #
    # I think this doesn't quite work if we don't confirm that we want the server shutdown.
    #   Oh well for now...
    ORIGINAL = None

    def shutdown_from_signal(*args, **kwargs):
        if ORIGINAL:
            ORIGINAL(*args, **kwargs)

        J_LOGGER.info("SERVER: Shutting down server")
        server.shutdown()

    ORIGINAL = signal.signal(signal.SIGINT, shutdown_from_signal)
