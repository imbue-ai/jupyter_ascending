import argparse
from pathlib import Path

from jupyter_ascending.handlers import jupyter_server
from jupyter_ascending.json_requests import GetStatusRequest


def send(file_name: str):
    file_name = str(Path(file_name).absolute())

    request_obj = GetStatusRequest(file_name=file_name)
    jupyter_server.request_notebook_command(request_obj)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")

    arguments = parser.parse_args()
    send(arguments.filename)
