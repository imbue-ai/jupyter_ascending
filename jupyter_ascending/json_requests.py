"""Defines messages and data payloads for the JSON-RPC client-server protocol
+used to send our custom messages to the Jupyter notebook.

TODO: dataclass looks to be depreciated. Replace with attr.define"""
from typing import Optional

from attr import dataclass


@dataclass
class JsonBaseRequest:
    file_name: str


@dataclass
class ExecuteRequest(JsonBaseRequest):
    cell_index: int
    contents: Optional[str]


@dataclass
class ExecuteAllRequest(JsonBaseRequest):
    pass


@dataclass
class RestartRequest(JsonBaseRequest):
    pass


@dataclass
class SyncRequest(JsonBaseRequest):
    contents: str


@dataclass
class GetStatusRequest(JsonBaseRequest):
    pass


@dataclass
class FocusCellRequest(JsonBaseRequest):
    cell_index: int
