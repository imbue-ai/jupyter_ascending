from functools import wraps
from http.server import BaseHTTPRequestHandler
from typing import Callable

from jsonrpcserver import dispatch
from jsonrpcserver import methods

from jupyter_ascending.logger import J_LOGGER


def _wrap_request(f: Callable, start_msg: str, close_msg: str):
    @wraps(f)
    @J_LOGGER.catch
    def wrapper(*args, **kwargs):
        J_LOGGER.debug("{}: {}", start_msg, f.__name__)

        result = f(*args, **kwargs)

        J_LOGGER.debug("{}: {}", close_msg, result)

        return result

    return wrapper


class ServerMethods:
    """
    Wrapper to make some things a bit nicer around jsonrpcserver.methods.Methods

    Adds auto logging and error catching so that you don't have to remember to do that.
    """

    def __init__(self, start_msg: str, close_msg: str):
        self.items = {}
        self.start_msg = start_msg
        self.close_msg = close_msg

    def add(self, f: Callable) -> Callable:
        self.items[f.__name__] = f

        return _wrap_request(f, self.start_msg, self.close_msg)


def generate_request_handler(name: str, methods: ServerMethods) -> BaseHTTPRequestHandler:
    @J_LOGGER.catch
    def do_POST(self):
        # Process request
        request = self.rfile.read(int(self.headers["Content-Length"])).decode()
        J_LOGGER.info("{} processing request:\n\t\t{}", name, request)

        response = dispatch(request, methods=methods)

        J_LOGGER.info("Got Response:\n\t\t{}", response)

        # Return response
        self.send_response(response.http_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(str(response).encode())

    def log_message(self, format, *args):
        J_LOGGER.debug(args)

    return type(
        f"{name}RequestHandler",
        (BaseHTTPRequestHandler,),
        {"allow_reuse_address": True, "do_POST": do_POST, "log_message": log_message},
    )
