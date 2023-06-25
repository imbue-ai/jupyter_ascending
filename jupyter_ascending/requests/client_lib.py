from typing import TypeVar

import attr
import requests
from jsonrpcclient import Ok
from jsonrpcclient import parse
from jsonrpcclient import request
from requests.exceptions import ConnectionError  # type: ignore

from jupyter_ascending._environment import EXECUTE_HOST_URL
from jupyter_ascending.handlers.server_extension import perform_notebook_request
from jupyter_ascending.json_requests import JsonBaseRequest

GenericJsonRequest = TypeVar("GenericJsonRequest", bound=JsonBaseRequest)


class RequestFailure(Exception):
    pass


def request_notebook_command(json_request: GenericJsonRequest):
    """This is a command to be used by the client libraries to send a command to this server.

    It calls unpacks the JsonRequest and calls `perform_notebook_request` defined above."""
    try:
        json = request(
            perform_notebook_request.__name__,
            params=dict(
                command_name=type(json_request).__name__,
                notebook_path=json_request.file_name,
                data=attr.asdict(json_request),
            ),
        )
        response = requests.post(EXECUTE_HOST_URL, json=json)
        response.raise_for_status()
        result = parse(response.json())

        if not isinstance(result, Ok):
            raise RequestFailure(f"JSONRPC request returned as failure: {result}")

    except ConnectionError as e:
        raise RequestFailure("Unable to connect to server. Perhaps notebook is not running?") from e
    except requests.exceptions.HTTPError as e:
        raise RequestFailure(
            "Unable to process request. Is jupyter-ascending installed in the server's python environment? Perhaps something else is running on this port?"
        ) from e
