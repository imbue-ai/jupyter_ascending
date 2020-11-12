import abc
from collections import defaultdict
from difflib import SequenceMatcher
from difflib import get_close_matches
from enum import Enum
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from typing import Union

import attr
import edlib

from jupyter_ascending.notebook.data_types import CellMovements
from jupyter_ascending.notebook.data_types import JupyterCell
from jupyter_ascending.notebook.data_types import Movement
from jupyter_ascending.notebook.data_types import NotebookContents
from jupyter_ascending.notebook.evolve import evolve_notebook_cells

Number = Union[int, float]


def _get_raw_contents(notebook: NotebookContents) -> Tuple[str, ...]:
    return tuple(x.complete_source for x in notebook.cells)


class OpCodes(Enum):
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"

    # Custom actions for us.
    COPY_OUTPUT = "copy_output"


@attr.dataclass
class OpCodeAction:
    op_code: OpCodes
    current_start_idx: int
    current_final_idx: int
    updated_start_idx: int
    updated_final_idx: int

    @property
    def current(self) -> Tuple[int, int]:
        return (self.current_start_idx, self.current_final_idx)

    @property
    def updated(self) -> Tuple[int, int]:
        return (self.updated_start_idx, self.updated_final_idx)


def opcode_merge_cell_contents(
    current_notebook: NotebookContents, updated_notebook: NotebookContents
) -> List[OpCodeAction]:
    raw_current_contents = _get_raw_contents(current_notebook)
    raw_updated_contents = _get_raw_contents(updated_notebook)

    sequence_matcher = SequenceMatcher(None, raw_current_contents, raw_updated_contents)

    current_cells_consumed: Set[int] = set()
    cells_to_update_text: List[int] = []

    opcode_results = []
    for (
        opcode,
        current_start_idx,
        current_final_idx,
        updated_start_idx,
        updated_final_idx,
    ) in sequence_matcher.get_opcodes():

        if opcode in {"replace", "insert"}:
            cells_to_update_text.extend(range(updated_start_idx, updated_final_idx))

        if opcode not in {"delete"}:
            current_cells_consumed.update(range(current_start_idx, current_final_idx))

        opcode_results.append(
            OpCodeAction(OpCodes(opcode), current_start_idx, current_final_idx, updated_start_idx, updated_final_idx)
        )

    current_cells_remaining = set(range(len(raw_current_contents))) - current_cells_consumed

    for updated_cell_index in cells_to_update_text:
        closest_match = get_close_matches(
            raw_updated_contents[updated_cell_index], [raw_current_contents[x] for x in current_cells_remaining], n=1
        )

        if closest_match:
            match = closest_match[0]

            for current_cell_idx in current_cells_remaining:
                if raw_current_contents[current_cell_idx] == match:
                    current_cells_remaining.remove(current_cell_idx)
                    # TODO: Maybe it makes sense to do plus 1 here. Off-by-one is hard
                    opcode_results.append(
                        OpCodeAction(
                            OpCodes("copy_output"),
                            current_cell_idx,
                            current_cell_idx,
                            updated_cell_index,
                            updated_cell_index,
                        )
                    )
                    break

    return opcode_results


def merge_cell_contents(
    current_notebook: NotebookContents, updated_notebook: NotebookContents
) -> Tuple[NotebookContents, CellMovements]:
    # TODO: change name of current_notebook to be remote notebook? some other name that makes it obvious
    if current_notebook.content_equals(updated_notebook):
        return current_notebook, CellMovements(movements=[])

    current_cell_stack = [x for x in current_notebook.cells]
    updated_cell_stack = [x for x in updated_notebook.cells]

    movements = []
    final_cells = []

    # 1. Check if we have cells that are exactly the same source
    #   We just update to the new index
    current_cells_to_remove = []
    for current_cell in current_cell_stack:
        for updated_cell in updated_cell_stack:
            if current_cell.source == updated_cell.source:

                # Create movements
                if current_cell.index != updated_cell.index:
                    movements.append(Movement(previous=current_cell.index, current=updated_cell.index))

                final_cells.append(attr.evolve(current_cell, index=updated_cell.index))

                # Remove at the end, since it's not good to modify iterators while iterating
                current_cells_to_remove.append(current_cell)

                updated_cell_stack.remove(updated_cell)
                break

    for cell in current_cells_to_remove:
        current_cell_stack.remove(cell)

    # 2. gather up all the differences between the remaining cells
    distancer = LevenshteinDistance

    distance_between_cells: Dict[JupyterCell, List[CellDistance]] = defaultdict(list)
    for current_cell in current_cell_stack:
        # TODO: What if all the distances are bad?
        # TODO: maybe use a different measure? like some confidence that they're the same
        for updated_cell in updated_cell_stack:
            if current_cell.source == updated_cell.source:
                assert False, f"{current_cell} / {updated_cell}::\n{final_cells}"

            distance = distancer.find_distance(current_cell.joined_source, updated_cell.joined_source)
            distance_between_cells[current_cell].append(CellDistance(distance, updated_cell))

        distance_between_cells[current_cell] = list(
            sorted(distance_between_cells[current_cell], key=distancer.sort_function)
        )

    # 3. Find most closely related cells (so, small distance)
    #       If I run out of updated_cell_stack, then we're done. No more cells to give
    #       If I run out of current_cell_stack, then we need to delete those (however that looks).

    def find_most_likely_cell(x):
        distance = distance_between_cells[x]

        return distancer.sort_function(distance[0])

    # TODO: This might be way too many loops?
    while current_cell_stack and distance_between_cells and updated_cell_stack:
        sorted_cell_list = sorted(current_cell_stack, key=find_most_likely_cell)
        current_cell = sorted_cell_list[0]

        cell_distances = distance_between_cells.pop(current_cell)
        best_updated_cell = next(x.cell for x in cell_distances if x.cell in updated_cell_stack)

        assert current_cell in current_cell_stack
        current_cell_stack.remove(current_cell)

        assert best_updated_cell in updated_cell_stack
        updated_cell_stack.remove(best_updated_cell)

        evolved_cell = attr.evolve(current_cell, index=best_updated_cell.index, source=best_updated_cell.source)
        final_cells.append(evolved_cell)

    # Any other updated cells we have must have been inserted.
    #   We can simply insert them into the final cells
    #   (Unless there is something I missed here...)
    while updated_cell_stack:
        final_cells.append(updated_cell_stack.pop())

    # Should have no more updated cells to input
    assert not updated_cell_stack

    return evolve_notebook_cells(current_notebook, final_cells), CellMovements(movements=movements)


@attr.dataclass
class CellDistance:
    distance: Number
    cell: JupyterCell


class BaseStringDistancer(abc.ABC):
    @staticmethod
    def find_distance(string_1: str, string_2: str) -> Number:
        raise NotImplementedError

    @staticmethod
    def sort_function(distance: CellDistance) -> Number:
        raise NotImplementedError


class LevenshteinDistance(BaseStringDistancer):
    @staticmethod
    def find_distance(string_1: str, string_2: str) -> int:
        # TODO: Maybe use jaro winkler instead
        return edlib.align(string_1, string_2)["editDistance"]

    @staticmethod
    def sort_function(distance: CellDistance) -> Number:
        return distance.distance
