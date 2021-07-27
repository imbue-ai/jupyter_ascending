import argparse
from pathlib import Path

from loguru import logger

from jupyter_ascending._environment import SYNC_EXTENSION
from jupyter_ascending.json_requests import SyncRequest
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.requests.client_lib import request_notebook_command


@logger.catch
def send(file_name: str):
    if f".{SYNC_EXTENSION}.py" not in file_name:
        return

    logger.info(f"Syncing File: {file_name}...")
    file_name = str(Path(file_name).absolute())

    with open(file_name, "r") as reader:
        raw_result = reader.read()

    request_obj = SyncRequest(file_name=file_name, contents=raw_result)
    request_notebook_command(request_obj)

    logger.info("... Complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    setup_logger()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()
    send(arguments.filename)
