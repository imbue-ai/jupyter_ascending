from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import attr


def optional_tuple(val) -> Optional[Tuple[Any, ...]]:
    if val is None:
        return None

    if isinstance(val, str):
        return (val,)

    return tuple(val)


# def frozen_dict(val) -> Optional[


@attr.s(frozen=True)
class JupyterCell:
    # TODO: Should probably be an enum
    cell_type: str = attr.ib()

    #: -1 for unknown
    #: otherwise which cell index they are.
    index: int = attr.ib()

    #: Note that source contains a list of strings,
    #:  but the strings (always?) have a new line at the end if they should have one at all.
    source: Tuple[str, ...] = attr.ib(converter=optional_tuple)

    #: Not currently filed?
    output: Optional[Tuple[str, ...]] = attr.ib(converter=optional_tuple)

    execution_count: Optional[int] = attr.ib(default=None)
    # metadata: Optional[Dict[str, Any]] = attr.ib(default=None, converter=frozen_dict)

    # occurs in higher versions of nbformat
    id: Optional[str] = attr.ib(default=None)

    @property
    def joined_source(self) -> str:
        return "".join(self.source)

    @property
    def complete_source(self) -> str:
        return f"{self.cell_type}::::{self.joined_source}"

    # def __eq__(self, o):
    #     if not isinstance(o, JupyterCell):
    #         return False

    #     return self.source == o.source and self.index == o.index and self.cell_type == o.cell_type

    # def __hash__(self):
    #     return (self.cell_type, self.index, self.source)


@attr.dataclass
class NotebookContents:
    cells: List[JupyterCell]

    # TODO: Make sure cells are in the right order

    def _cell_insides(self):
        return [(x.index, x.cell_type, x.source) for x in self.cells]

    def content_equals(self, other: "NotebookContents") -> bool:
        return self._cell_insides() == other._cell_insides()


@attr.dataclass
class Movement:
    previous: int
    current: int


@attr.dataclass
class CellMovements:
    movements: List[Movement]
