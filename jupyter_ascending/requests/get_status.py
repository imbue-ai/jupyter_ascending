import argparse
from pathlib import Path

from jupyter_ascending.json_requests import GetStatusRequest
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.requests.client_lib import request_notebook_command


def send(file_name: str):
    file_name = str(Path(file_name).absolute())

    request_obj = GetStatusRequest(file_name=file_name)
    request_notebook_command(request_obj)


if __name__ == "__main__":
    setup_logger()
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()
    send(arguments.filename)
