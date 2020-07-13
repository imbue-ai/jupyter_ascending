import threading
from http.server import HTTPServer
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypeVar

import attr
from jsonrpcclient import request

from jupyter_ascending.handlers import ServerMethods
from jupyter_ascending.handlers import generate_request_handler
from jupyter_ascending.handlers.jupyter_notebook import handle_execute_request
from jupyter_ascending.handlers.jupyter_notebook import handle_get_status_request
from jupyter_ascending.handlers.jupyter_notebook import handle_sync_request
from jupyter_ascending.json_requests import ExecuteRequest
from jupyter_ascending.json_requests import GetStatusRequest
from jupyter_ascending.json_requests import JsonBaseRequest
from jupyter_ascending.json_requests import SyncRequest
from jupyter_ascending.logger import J_LOGGER
from jupyter_ascending._environment import EXECUTE_HOST_LOCATION
from jupyter_ascending._environment import EXECUTE_HOST_URL

GenericJsonRequest = TypeVar("GenericJsonRequest", bound=JsonBaseRequest)

_REGISTERED_SERVERS: Dict[str, int] = {}


multiplexer_methods = ServerMethods("JupyterServer Start", "JupyterServer Close")


@multiplexer_methods.add
def register_notebook_server(notebook_path: str, port_number: int) -> None:
    register_server(notebook_path=notebook_path, port_number=port_number)


@multiplexer_methods.add
def perform_notebook_request(notebook_path: str, command_name: str, data: Dict[str, Any]) -> None:
    J_LOGGER.debug("Performing notebook request... ")

    notebook_server = get_server_for_notebook(notebook_path)
    if notebook_server is None:
        J_LOGGER.warning("==> Unable to process request")
        J_LOGGER.warning("==> {}", _REGISTERED_SERVERS)
        return

    request(notebook_server, command_name, data=data)


JupyterServerRequestHandler = generate_request_handler("JupyterServer", multiplexer_methods)


def register_server(notebook_path: str, port_number: int) -> None:
    J_LOGGER.info("Registering notebook {notebook} on port {port}", notebook=notebook_path, port=port_number)

    _REGISTERED_SERVERS[notebook_path] = port_number

    J_LOGGER.debug("Updated notebook mappings: {}", _REGISTERED_SERVERS)


def get_server_for_notebook(notebook_path: str) -> Optional[str]:
    # Normalize to notebook path
    notebook_path = notebook_path.replace(".synced.py", ".synced.ipynb")

    J_LOGGER.debug("Finding server for notebook_path, script_path: {}", notebook_path)

    potential_notebooks: List[str] = []
    for registered_name in _REGISTERED_SERVERS:
        if registered_name in notebook_path:
            potential_notebooks.append(registered_name)

    if len(potential_notebooks) > 1:
        J_LOGGER.warning("Found more than one notebook {}, {}", notebook_path, potential_notebooks)
        return None
    elif len(potential_notebooks) == 1:
        notebook_port = _REGISTERED_SERVERS[potential_notebooks[0]]

        J_LOGGER.debug("Found server at port {}", notebook_port)
        return f"http://localhost:{notebook_port}"
    else:
        J_LOGGER.warning("Could not find server for notebook_path: {}", notebook_path)
        return None


def request_notebook_command(json_request: GenericJsonRequest):
    request(
        EXECUTE_HOST_URL,
        perform_notebook_request.__name__,
        command_name=_map_json_request_to_function_name(json_request),
        notebook_path=json_request.file_name,
        data=attr.asdict(json_request),
    )


def _map_json_request_to_function_name(json_request: GenericJsonRequest) -> str:
    # TODO: Move this to a dictionary, and check all non-abstract children of BaseJsonRequest

    if isinstance(json_request, ExecuteRequest):
        return handle_execute_request.__name__
    elif isinstance(json_request, SyncRequest):
        return handle_sync_request.__name__
    elif isinstance(json_request, GetStatusRequest):
        return handle_get_status_request.__name__
    else:
        assert False, json_request


def start_server_in_thread():
    server_executor = HTTPServer(EXECUTE_HOST_LOCATION, JupyterServerRequestHandler)
    server_executor_thread = threading.Thread(target=server_executor.serve_forever, args=tuple())
    server_executor_thread.start()

    J_LOGGER.info("Successfully started multiplexer server")

    return server_executor
