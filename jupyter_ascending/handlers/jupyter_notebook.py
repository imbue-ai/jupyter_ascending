"""
This file contains code for the JSON-RPC server we run alongside each .sync.ipynb notebook.

It receives messages from `jupyter_server.py` and takes the appropriate action in the notebook.
"""
import threading
import time
from http.server import HTTPServer
from inspect import signature
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type

import jupytext
from IPython.display import display
from ipykernel.comm import Comm
from jsonrpcclient import request
from loguru import logger

from jupyter_ascending._environment import EXECUTE_HOST_URL
from jupyter_ascending.handlers import ServerMethods
from jupyter_ascending.handlers import generate_request_handler
from jupyter_ascending.handlers.server_extension import register_notebook_server
from jupyter_ascending.json_requests import ExecuteAllRequest
from jupyter_ascending.json_requests import ExecuteRequest
from jupyter_ascending.json_requests import FocusCellRequest
from jupyter_ascending.json_requests import GetStatusRequest
from jupyter_ascending.json_requests import RestartRequest
from jupyter_ascending.json_requests import SyncRequest
from jupyter_ascending.notebook.data_types import JupyterCell
from jupyter_ascending.notebook.data_types import NotebookContents
from jupyter_ascending.notebook.merge import OpCodeAction
from jupyter_ascending.notebook.merge import OpCodes
from jupyter_ascending.notebook.merge import opcode_merge_cell_contents
from jupyter_ascending.utils import find_free_port

COMM_NAME = "AUTO_SYNC::notebook"

notebook_server_methods = ServerMethods("JupyterNotebook Start", "JupyterNotebook Close")

merge_complete = False

lock = threading.Lock()


@logger.catch
def start_notebook_server_in_thread(notebook_name: str, status_widget=None):
    """
    Args:
        notebook_name: The name of the notebook you want to be syncing in this process.
    """

    notebook_path = Path(notebook_name).absolute()

    # TODO: This might be a race condition if a bunch of these started at once...
    notebook_server_port = find_free_port()

    notebook_executor = HTTPServer(("localhost", notebook_server_port), NotebookKernelRequestHandler,)
    notebook_executor_thread = threading.Thread(target=notebook_executor.serve_forever, args=tuple())
    notebook_executor_thread.start()

    logger.info("IPYTHON: Registering notebook {}", notebook_path)
    request(
        EXECUTE_HOST_URL,
        register_notebook_server.__name__,
        # Params
        notebook_path=str(notebook_path),
        port_number=notebook_server_port,
    )
    logger.info("==> Success")


def dispatch_json_request(f):
    """
    A kinda weird decorator attempting to remove some boilerplate in the following funcs.
    Automatically dispatch a json request based on the request_type.

    Adds it to notebook_server_methods
    """

    # Get the type from the first argument of the function.
    #   This will define the name that we use to generate the method handling.
    request_type = signature(f).parameters["request_type"].annotation.__args__[0]

    def wrapped(data: Dict) -> str:
        return f(request_type, data)

    wrapped.__name__ = request_type.__name__

    return notebook_server_methods.add(wrapped)


@dispatch_json_request
def handle_execute_request(request_type: Type[ExecuteRequest], data: dict) -> str:
    """JSON-RPC request handler for 'execute cell'"""
    request = request_type(**data)

    comm = make_comm()
    execute_cell_contents(comm, request.cell_index)

    return f"Executing cell `{request.cell_index}`"


@dispatch_json_request
def handle_execute_all_request(request_type: Type[ExecuteAllRequest], data: dict) -> str:
    """JSON-RPC request handler for 'execute all cells'"""
    request = request_type(**data)

    # TODO: Remind myself why I don't need to say the filename here...
    comm = make_comm()
    execute_all_cells(comm)

    return f"Executing all cells in {request.file_name}"


@dispatch_json_request
def handle_sync_request(request_type: Type[SyncRequest], data: dict) -> str:
    """JSON-RPC request handler for 'sync'"""
    global merge_complete
    merge_complete = False
    request = request_type(**data)

    # We lock here because updating the notebook isn't threadsafe.
    # If we got two sync requests simultaneously without a lock,
    # bad things might happen (eg duplicated inserts/deletes).
    with lock:
        comm = make_comm()

        result = jupytext.reads(request.contents, fmt="py:percent")
        update_cell_contents(comm, result)

    return "Syncing all cells"


@dispatch_json_request
def handle_focus_cell_request(request_type: Type[FocusCellRequest], data: dict) -> str:
    """JSON-RPC request handler for 'focus cell'"""
    request = request_type(**data)

    print(request)
    raise NotImplementedError


@dispatch_json_request
def handle_get_status_request(request_type: Type[GetStatusRequest], data: dict) -> str:
    """JSON-RPC request handler for 'get status'"""
    logger.info("Attempting get_status")

    comm = make_comm()
    comm.send({"command": "get_status"})

    logger.info("Sent get_status")

    return f"Updating status"


@dispatch_json_request
def handle_restart_request(request_type: Type[RestartRequest], data: dict) -> str:
    """JSON-RPC request handler for 'restart'"""
    request = request_type(**data)

    comm = make_comm()
    comm.send({"command": "restart_kernel"})
    logger.info("Sent restart_kernel")

    return f"Restarting kernel in {request.file_name}"


NotebookKernelRequestHandler = generate_request_handler("NotebookKernel", notebook_server_methods)


def make_comm():
    """A comm is a Jupyter object for communicating between a notebook and kernel.

    Set up this object with event handlers."""
    global merge_complete

    logger.info("IPYTHON: Registering Comms")

    comm_target_name = COMM_NAME

    jupyter_comm = Comm(target_name=comm_target_name)

    def _get_command(msg) -> Optional[str]:
        return msg["content"]["data"].get("command", None)

    @jupyter_comm.on_msg
    def _recv(msg):
        global merge_complete
        if _get_command(msg) == "merge_notebooks":
            logger.info("GOT UPDATE STATUS")
            merge_notebooks(jupyter_comm, msg["content"]["data"])
            return

        if _get_command(msg) == "merge_complete":
            logger.info("GOT MERGE COMPLETE")
            merge_complete = True
            return

        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        logger.info(msg)
        logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    logger.info("==> Success")

    return jupyter_comm


def update_cell_contents(comm: Comm, result: Dict[str, Any]) -> None:
    # logger.info(Javascript("Jupyter.notebook.get_cells()"))
    def _transform_jupytext_cells(jupytext_cells) -> List[Dict[str, Any]]:
        """TODO: what does this do?"""
        return [
            {"index": i, "output": [], **{k: v for (k, v) in x.items() if k not in {"outputs", "metadata"}}}
            for i, x in enumerate(result["cells"])
        ]

    comm.send({"command": "start_sync_notebook", "cells": _transform_jupytext_cells(result["cells"])})

    # Wait for the merge_complete flag to get set in the callback.
    # This way we don't release the lock before syncing is done.
    for i in range(500):
        if merge_complete:
            return
        time.sleep(0.01)
    else:
        logger.warning("Timed out waiting for syncing to complete.")
    # contents = NotebookContents(cells=result["cells"])


def get_output_text(javascript_cell) -> Optional[str]:
    """Get cell output or return None if no output?"""
    output_tuple = javascript_cell.get("outputs", tuple())
    if not output_tuple:
        return None

    output = output_tuple[0]

    if output.get("data", None):
        data = output["data"]

        if isinstance(data, dict):
            if data.get("text/plain", None):
                return data["text/plain"]

    if output.get("text", None):
        return output["text"]

    return None


@logger.catch(reraise=True)
def merge_notebooks(comm: Comm, result: Dict[str, Any]) -> None:
    javascript_cells = result["javascript_cells"]
    current_notebook = NotebookContents(
        cells=[
            JupyterCell(
                index=i,
                cell_type=x["cell_type"],
                source=x["source"],
                output=get_output_text(x),
                # metadata=x["metadata"],
            )
            for i, x in enumerate(javascript_cells)
        ]
    )

    new_notebook = NotebookContents(cells=[JupyterCell(**x) for x in result["new_notebook"]])

    opcodes = opcode_merge_cell_contents(current_notebook, new_notebook)
    logger.info("Performing Opcodes...")
    logger.info(opcodes)

    net_shift = 0
    for op_action in opcodes:
        net_shift = perform_op_code(comm, op_action, current_notebook, new_notebook, net_shift)

    logger.info("sending finish_merge command")
    comm.send({"command": "finish_merge"})


def perform_op_code(
    comm: Comm,
    op_action: OpCodeAction,
    current_notebook: NotebookContents,
    updated_notebook: NotebookContents,
    net_shift: int,
) -> int:
    """
    net_shift (int): Tracks the net shift of previous op codes since we can't apply all the operations at the same time to jupyter,
                        since it does not have that kind of editting model.

                        So what we do is make sure that as we delete and insert, we keep track of the shifts that have happened thus far.
                        Given this shift, we will shift the actions that we tell Jupyter notebook to do.
    """

    if op_action.op_code == OpCodes.EQUAL:
        pass

    elif op_action.op_code == OpCodes.DELETE:
        logger.info(f"Performing Delete: {op_action}")

        # Since deletion is a bit goofy for jupyter, so it has to be adjusted by net shift thus far.
        cells_to_delete = [x + net_shift for x in range(*op_action.current)]
        comm.send({"command": "op_code__delete_cells", "cell_indices": cells_to_delete})

        net_shift = net_shift - len(cells_to_delete)

    elif op_action.op_code == OpCodes.INSERT:
        logger.info(f"Performing Insert: {op_action}")

        cells_to_insert = list(range(*op_action.updated))
        for cell_number in cells_to_insert:
            comm.send(
                {
                    "command": "op_code__insert_cell",
                    "cell_number": cell_number,
                    "cell_type": updated_notebook.cells[cell_number].cell_type,
                    "cell_contents": updated_notebook.cells[cell_number].joined_source,
                }
            )

        net_shift = net_shift + len(cells_to_insert)

    elif op_action.op_code == OpCodes.REPLACE:
        # Keep track of what the current cells looked like before.
        current_cells = list(range(*op_action.current))
        updated_cells = list(range(*op_action.updated))

        for cell_number in updated_cells:
            # If we have current cells we're replacing, do that.
            if current_cells:
                current_cells.pop(0)

                comm.send(
                    {
                        "command": "op_code__replace_cell",
                        "cell_number": cell_number,
                        "cell_type": updated_notebook.cells[cell_number].cell_type,
                        "cell_contents": updated_notebook.cells[cell_number].joined_source,
                    }
                )
            # Otherwise, we have new cells to insert so we don't overwrite existing cells
            else:
                net_shift = perform_op_code(
                    comm,
                    OpCodeAction(
                        op_code=OpCodes.INSERT,
                        # NOTE: This is intentionally the last index for both of these
                        current_start_idx=op_action.current_final_idx,
                        current_final_idx=op_action.current_final_idx,
                        updated_start_idx=cell_number,
                        updated_final_idx=cell_number + 1,
                    ),
                    current_notebook,
                    updated_notebook,
                    net_shift,
                )

        # If we have cells left over from the replace (i.e. 1-4 replaced with 1-2),
        #   then we need to delete the rest of them.
        if current_cells:
            net_shift = perform_op_code(
                comm,
                OpCodeAction(
                    op_code=OpCodes.DELETE,
                    current_start_idx=current_cells[0],
                    current_final_idx=current_cells[-1] + 1,
                    # NOTE: This is intentionally the last index for both of these
                    updated_start_idx=op_action.updated_final_idx,
                    updated_final_idx=op_action.updated_final_idx,
                ),
                current_notebook,
                updated_notebook,
                net_shift,
            )

    else:
        raise NotImplementedError

    return net_shift


def execute_cell_contents(comm: Comm, cell_number: int) -> None:
    comm.send({"command": "execute", "cell_number": cell_number})


def execute_all_cells(comm: Comm) -> None:
    comm.send({"command": "execute_all"})
