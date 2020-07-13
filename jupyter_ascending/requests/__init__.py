"""
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
class SyncRequest(JsonBaseRequest):
    contents: str


@dataclass
class GetStatusRequest(JsonBaseRequest):
    pass


@dataclass
class FocusCellRequest(JsonBaseRequest):
    cell_index: int
"""
