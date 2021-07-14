from notebook.utils import url_path_join  # type: ignore
from notebook.base.handlers import IPythonHandler  # type: ignore

from jsonrpcserver import dispatch
from jsonrpcserver import method

from typing import Any
from typing import Dict
from typing import Optional

from jsonrpcclient import request

from jupyter_ascending.errors import UnableToFindNotebookException
from jupyter_ascending.logger import J_LOGGER
from jupyter_ascending._environment import SYNC_EXTENSION
from pathlib import Path
from jupyter_ascending.functional import get_matching_tail_tokens


_REGISTERED_SERVERS: Dict[str, int] = {}


def _clear_registered_servers():
    global _REGISTERED_SERVERS

    _REGISTERED_SERVERS = {}


class JupyterAscendingHandler(IPythonHandler):
    # def get(self):
    #     print("got get request!")
    #     self.finish('Hello, world!')

    def post(self) -> None:
        """We receive commands as HTTP POST requests.

        TODO: might want to convert this to async in the future
        (tornado and jsonrpcserver support asyncio)"""
        request = self.request.body.decode()
        response = dispatch(request)
        J_LOGGER.info("Got Response:\n\t\t{}", response)
        if response.wanted:
            self.write(str(response))

    def check_xsrf_cookie(self):
        """Disable XSRF cookie checking on this request type"""
        pass

def load_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/jupyter_ascending')
    web_app.add_handlers(host_pattern, [(route_pattern, JupyterAscendingHandler)])



@method
def register_notebook_server(notebook_path: str, port_number: int) -> None:
    J_LOGGER.info("Registering notebook {notebook} on port {port}", notebook=notebook_path, port=port_number)

    _REGISTERED_SERVERS[notebook_path] = port_number

    J_LOGGER.debug("Updated notebook mappings: {}", _REGISTERED_SERVERS)


@method
def perform_notebook_request(notebook_path: str, command_name: str, data: Dict[str, Any]) -> Optional[Dict]:
    """Receives a command from the client library, picks the notebook that matches
    the filepath, and forwards the command along to that notebook."""
    J_LOGGER.debug("Performing notebook request... ")

    try:
        notebook_server = get_server_for_notebook(notebook_path)
    except UnableToFindNotebookException:
        J_LOGGER.warning(f"Unabled to find {notebook_path} in {_REGISTERED_SERVERS}")
        return {"success": False, "notebook_path": notebook_path}

    request(notebook_server, command_name, data=data)


def _make_url(notebook_port: int):
    return f"http://localhost:{notebook_port}"

def get_server_for_notebook(notebook_str: str) -> Optional[str]:
    """Get the URL to the server running on the Jupyter notebook that best matches this filename."""
    # Normalize to notebook path
    notebook_str = notebook_str.replace(f".{SYNC_EXTENSION}.py", f".{SYNC_EXTENSION}.ipynb")
    J_LOGGER.debug("Finding server for notebook_str, script_path: {}", notebook_str)

    notebook_path = Path(notebook_str)

    def get_score_for_name(registered_name: str) -> int:
        """
        Note that it is matching on parts of a path

        Returns the consecutive count of matching parts of a path, from the end toward the start.

        registered ['tmp', 'notebooks', 'myfile.py']
        notebook   ['opt', 'notebooks', 'myfile.py']
         -> 2

        registered ['a', 'b', 'c']
        notebook   ['a', 'b', 'd']
         -> 0

        """
        return len(get_matching_tail_tokens(notebook_path.parts, Path(registered_name).parts))

    score_by_name = {x: get_score_for_name(x) for x in _REGISTERED_SERVERS.keys()}

    if len(score_by_name) == 0:
        raise UnableToFindNotebookException(f"No registered notebooks")

    max_score = max(score_by_name.values())

    if max_score <= 0:
        raise UnableToFindNotebookException(f"Could not find server for notebook_str: {notebook_str}")

    # Only found one reasonable notebook.
    best_scores = [k for k, v in score_by_name.items() if v == max_score]

    if len(best_scores) == 1:
        notebook_port = _REGISTERED_SERVERS[best_scores[0]]

        J_LOGGER.debug("Found server at port {}", notebook_port)
        return _make_url(notebook_port)
    else:
        raise UnableToFindNotebookException(f"Could not find server for notebook_str: {notebook_str}")