import argparse
from pathlib import Path

from jupyter_ascending.handlers import jupyter_server
from jupyter_ascending.json_requests import ExecuteAllRequest
from jupyter_ascending.logger import J_LOGGER


def send(file_name: str):
    J_LOGGER.info(f"Executing all cells in file: {file_name}...")
    file_name = str(Path(file_name).absolute())

    request_obj = ExecuteAllRequest(file_name=file_name)
    jupyter_server.request_notebook_command(request_obj)

    J_LOGGER.info("... Complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()

    send(arguments.filename)
