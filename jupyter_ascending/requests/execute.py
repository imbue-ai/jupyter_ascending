import argparse
from functools import partial
from pathlib import Path

from jupyter_ascending.handlers import jupyter_server
from jupyter_ascending.json_requests import ExecuteRequest
from jupyter_ascending.logger import J_LOGGER

CELL_SEPARATOR = "# %%"


def send(file_name: str, line_number: int, *args, **kwargs):
    J_LOGGER.debug("Starting execute request")

    # Always pass absolute path
    file_name = str(Path(file_name).absolute())

    request_obj = partial(ExecuteRequest, file_name=file_name, contents="")

    cell_index = -1
    with open(file_name, "r") as reader:
        for index, line in enumerate(reader):
            if line.startswith(CELL_SEPARATOR):
                J_LOGGER.debug(f"Found another new cell on line number: {index}")
                cell_index += 1
                J_LOGGER.debug(f"    New cell index {cell_index}")

            # No need to loop through the whole file, just execute when we get there
            if index == int(line_number):
                break

    final_request = request_obj(cell_index=cell_index)
    J_LOGGER.info(f"Sending request with {final_request}")
    jupyter_server.request_notebook_command(final_request)
    J_LOGGER.info("... Complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")
    parser.add_argument("--linenumber", help="Line number that the cursor is currently on")

    arguments = parser.parse_args()

    send(arguments.filename, arguments.linenumber)
