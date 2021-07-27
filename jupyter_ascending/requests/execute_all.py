import argparse
from pathlib import Path

from loguru import logger

from jupyter_ascending.json_requests import ExecuteAllRequest
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.requests.client_lib import request_notebook_command
from jupyter_ascending.requests.sync import send as sync_send


def send(file_name: str):
    logger.info(f"Executing all cells in file: {file_name}...")
    file_name = str(Path(file_name).absolute())

    request_obj = ExecuteAllRequest(file_name=file_name)
    request_notebook_command(request_obj)

    logger.info("... Complete")


if __name__ == "__main__":
    setup_logger()
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()

    # Sync code first
    sync_send(arguments.filename)
    send(arguments.filename)
