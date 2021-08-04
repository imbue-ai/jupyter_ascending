from functools import wraps
from http.server import BaseHTTPRequestHandler
from typing import Callable

from jsonrpcserver import dispatch
from jsonrpcserver import methods
from loguru import logger


def _wrap_request(f: Callable, start_msg: str, close_msg: str):
    @wraps(f)
    @logger.catch
    def wrapper(*args, **kwargs):
        logger.debug("{}: {}", start_msg, f.__name__)

        result = f(*args, **kwargs)

        logger.debug("{}: {}", close_msg, result)

        return result

    return wrapper


class ServerMethods:
    """
    Wrapper to make some things a bit nicer around jsonrpcserver.methods.Methods

    Basically our own version of jsonrpcserver.methods.Methods, wrapping each method with auto
    logging and error catching so that you don't have to remember to do that.
    """

    def __init__(self, start_msg: str, close_msg: str):
        self.items = {}
        self.start_msg = start_msg
        self.close_msg = close_msg

    def add(self, f: Callable) -> Callable:
        self.items[f.__name__] = f

        return _wrap_request(f, self.start_msg, self.close_msg)


def generate_request_handler(name: str, methods: ServerMethods) -> BaseHTTPRequestHandler:
    """Build a handler to respond to HTTP POST requests containing JSON-RPC messages.

    Will call jsonrpcserver.dispatch to dispatch the request to the appropriate handler.

    TODO: why this weird construction vs a simple subclass?
        - to be able to specify a custom class name, i think. but why do we need that?
    """

    @logger.catch
    def do_POST(self):
        # Process request
        request = self.rfile.read(int(self.headers["Content-Length"])).decode()
        logger.info("{} processing request:\n\t\t{}", name, request)

        # Dispatch the RPC request to the right function and get the function's response.
        response = dispatch(request, methods=methods)

        logger.info("Got Response:\n\t\t{}", response)

        # Return response
        self.send_response(response.http_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(str(response).encode())

    def log_message(self, format, *args):
        logger.debug(args)

    return type(
        f"{name}RequestHandler",
        (BaseHTTPRequestHandler,),
        {"allow_reuse_address": True, "do_POST": do_POST, "log_message": log_message},
    )
