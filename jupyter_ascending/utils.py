import json
import os
import socket
import urllib.request
from contextlib import closing

import ipykernel  # type: ignore
from notebook import notebookapp  # type: ignore


def get_name_from_python():
    """
    Returns the absolute path of the Notebook or None if it cannot be determined

    BUG: I think it currently doesn't _really_ return the absolute path, but it returns enough of it to be good I think.

    NOTE: works only when the security is token-based or there is also no password
    """
    connection_file = os.path.basename(ipykernel.get_connection_file())
    kernel_id = connection_file.split("-", 1)[1].split(".")[0]

    for srv in notebookapp.list_running_servers():
        try:
            if srv["token"] == "" and not srv["password"]:  # No token and no password, ahem...
                req = urllib.request.urlopen(srv["url"] + "api/sessions")
            else:
                req = urllib.request.urlopen(srv["url"] + "api/sessions?token=" + srv["token"])
            sessions = json.load(req)
            for sess in sessions:
                if sess["kernel"]["id"] == kernel_id:
                    return os.path.join(srv["notebook_dir"], sess["notebook"]["path"])
        except:
            pass  # There may be stale entries in the runtime directory

    return ""


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
