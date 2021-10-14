import argparse
import re
from functools import partial
from pathlib import Path
from typing import List

from loguru import logger

from jupyter_ascending.json_requests import ExecuteRequest
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.requests.client_lib import request_notebook_command
from jupyter_ascending.requests.sync import send as sync_send

CELL_SEPARATOR_PATTERNS = [
    re.compile(r"#\s*%%"),
    re.compile(r"#\s*\+\+"),
]


def _find_cell_number(lines: List[str], line_number: int) -> int:
    # We need to split cells the same way that jupytext does so that our cell numbers line up.
    # Unfortunately there's not an obvious way to just use the jupytext parser.

    # The default case has a # %% on the first line. The first cell starts after this.
    # A second case has no # %% before code begins. The first cell starts immediately.
    # A third case has a single blank line before the # %%. The blank line is its own cell.
    if any(pat.match(lines[0]) for pat in CELL_SEPARATOR_PATTERNS):
        cell_index = -1
    else:
        cell_index = 0

    for index, line in enumerate(lines):
        if any(pat.match(line) for pat in CELL_SEPARATOR_PATTERNS):
            logger.debug(f"Found another new cell on line number: {index}")
            cell_index += 1
            logger.debug(f"    New cell index {cell_index}")

        # Found line number, quit
        if index == int(line_number):
            break

    return cell_index


def send(file_name: str, line_number: int, *args, **kwargs):
    logger.debug("Starting execute request")

    # Always pass absolute path
    file_name = str(Path(file_name).absolute())

    request_obj = partial(ExecuteRequest, file_name=file_name, contents="")

    with open(file_name, "r") as reader:
        lines = reader.readlines()

    cell_index = _find_cell_number(lines, line_number)

    final_request = request_obj(cell_index=cell_index)
    logger.info(f"Sending request with {final_request}")
    request_notebook_command(final_request)
    logger.info("... Complete")


if __name__ == "__main__":
    setup_logger()
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")
    parser.add_argument("--linenumber", help="Line number that the cursor is currently on")

    arguments = parser.parse_args()

    # Sync code first
    sync_send(arguments.filename)
    send(arguments.filename, arguments.linenumber)
