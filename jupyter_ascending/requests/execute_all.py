import argparse
from pathlib import Path

from jupyter_ascending.json_requests import ExecuteAllRequest
from jupyter_ascending.logger import J_LOGGER
from jupyter_ascending.requests.client_lib import request_notebook_command
from jupyter_ascending.requests.sync import send as sync_send


def send(file_name: str):
    J_LOGGER.info(f"Executing all cells in file: {file_name}...")
    file_name = str(Path(file_name).absolute())

    request_obj = ExecuteAllRequest(file_name=file_name)
    request_notebook_command(request_obj)

    J_LOGGER.info("... Complete")


if __name__ == "__main__":
    J_LOGGER.disable("__main__")
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()

    # Sync code first
    sync_send(arguments.filename)
    send(arguments.filename)
