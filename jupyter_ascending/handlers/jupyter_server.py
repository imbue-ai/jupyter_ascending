import threading
from http.server import HTTPServer
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import TypeVar

import attr
from jsonrpcclient import request
from jsonrpcclient.exceptions import ReceivedNon2xxResponseError
from requests.exceptions import ConnectionError

from jupyter_ascending._environment import EXECUTE_HOST_LOCATION
from jupyter_ascending._environment import EXECUTE_HOST_URL
from jupyter_ascending.errors import UnableToFindNotebookException
from jupyter_ascending.functional import get_matching_tail_tokens
from jupyter_ascending.handlers import ServerMethods
from jupyter_ascending.handlers import generate_request_handler
from jupyter_ascending.json_requests import JsonBaseRequest
from jupyter_ascending.logger import J_LOGGER

GenericJsonRequest = TypeVar("GenericJsonRequest", bound=JsonBaseRequest)
T = TypeVar("T")

_REGISTERED_SERVERS: Dict[str, int] = {}


def _clear_registered_servers():
    global _REGISTERED_SERVERS

    _REGISTERED_SERVERS = {}


def _make_url(notebook_port: int):
    return f"http://localhost:{notebook_port}"


multiplexer_methods = ServerMethods("JupyterServer Start", "JupyterServer Close")


@multiplexer_methods.add
def register_notebook_server(notebook_path: str, port_number: int) -> None:
    register_server(notebook_path=notebook_path, port_number=port_number)


@multiplexer_methods.add
def perform_notebook_request(notebook_path: str, command_name: str, data: Dict[str, Any]) -> Optional[Dict]:
    J_LOGGER.debug("Performing notebook request... ")

    try:
        notebook_server = get_server_for_notebook(notebook_path)
    except UnableToFindNotebookException:
        J_LOGGER.warning(f"Unabled to find {notebook_path} in {_REGISTERED_SERVERS}")
        return {"success": False, "notebook_path": notebook_path}

    request(notebook_server, command_name, data=data)

    return None


JupyterServerRequestHandler = generate_request_handler("JupyterServer", multiplexer_methods)


def register_server(notebook_path: str, port_number: int) -> None:
    J_LOGGER.info("Registering notebook {notebook} on port {port}", notebook=notebook_path, port=port_number)

    _REGISTERED_SERVERS[notebook_path] = port_number

    J_LOGGER.debug("Updated notebook mappings: {}", _REGISTERED_SERVERS)


def get_server_for_notebook(notebook_str: str) -> Optional[str]:
    # Normalize to notebook path
    notebook_str = notebook_str.replace(".synced.py", ".synced.ipynb")
    J_LOGGER.debug("Finding server for notebook_str, script_path: {}", notebook_str)

    notebook_path = Path(notebook_str)

    def get_score_for_name(registered_name: str) -> int:
        """
        Returns the consecutive count of matching parts of a path, from the end toward the start.

        registered ['a', 'b', 'c']
        notebook   ['x', 'b', 'c']
         -> 2

        registered ['a', 'b', 'c']
        notebook   ['a', 'b', 'd']
         -> 0

        """
        return len(get_matching_tail_tokens(notebook_path.parts, Path(registered_name).parts))

    match_scores = list(filter(lambda x: x > 0, map(get_score_for_name, _REGISTERED_SERVERS)))

    if not match_scores:
        raise UnableToFindNotebookException(f"Could not find server for notebook_str: {notebook_str}")

    max_score = max(match_scores)

    # Only found one reasonable notebook.
    best_scores = list(filter(lambda scored_name: scored_name[0] == max_score, zip(match_scores, _REGISTERED_SERVERS)))

    if len(best_scores) == 1:
        notebook_port = _REGISTERED_SERVERS[best_scores.pop()[1]]

        J_LOGGER.debug("Found server at port {}", notebook_port)
        return _make_url(notebook_port)
    else:
        raise UnableToFindNotebookException(f"Could not find server for notebook_str: {notebook_str}")


def request_notebook_command(json_request: GenericJsonRequest):
    try:
        result = request(
            EXECUTE_HOST_URL,
            perform_notebook_request.__name__,
            command_name=type(json_request).__name__,
            notebook_path=json_request.file_name,
            data=attr.asdict(json_request),
        )

        if not result.data.result:
            return

        if not result.data.result.get("success", True):
            raise Exception(f"Failed to complete request. {result.data}")

    except ConnectionError as e:
        J_LOGGER.error(f"Unable to connect to server. Perhaps notebook is not running? {e}")
    except ReceivedNon2xxResponseError as e:
        J_LOGGER.error(f"Unable to process request. Perhaps something else is running on this port? {e}")


def start_server_in_thread():
    try:
        server_executor = HTTPServer(EXECUTE_HOST_LOCATION, JupyterServerRequestHandler)
    except OSError:
        print(f"It appears you already are using {EXECUTE_HOST_LOCATION}")
        print("Use the environment variable: 'JUPYTER_ASCENDING_EXECUTE_PORT' to set a new port")

        return

    server_executor_thread = threading.Thread(target=server_executor.serve_forever, args=tuple())
    server_executor_thread.start()

    J_LOGGER.info("Successfully started multiplexer server")

    return server_executor
