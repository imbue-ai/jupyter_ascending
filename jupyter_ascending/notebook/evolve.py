from typing import List

import attr

from jupyter_ascending.notebook.data_types import JupyterCell
from jupyter_ascending.notebook.data_types import NotebookContents


def evolve_notebook_cells(contents: NotebookContents, new_cells: List[JupyterCell]) -> NotebookContents:
    assert len(new_cells) == len(set(x.index for x in new_cells)), "Must have unique indeces"

    return attr.evolve(contents, cells=list(sorted(new_cells, key=lambda x: x.index)))


def evolve_cell_source(contents: NotebookContents, index: int, source: List[str]) -> NotebookContents:
    new_cells: List[JupyterCell] = []
    for cell in contents.cells:
        if cell.index == index:
            new_cells.append(attr.evolve(cell, source=source))
        else:
            new_cells.append(cell)

    return evolve_notebook_cells(contents, new_cells)


def evolve_cell_type(contents: NotebookContents, index: int, cell_type: str) -> NotebookContents:
    new_cells: List[JupyterCell] = []
    for cell in contents.cells:
        if cell.index == index:
            new_cells.append(attr.evolve(cell, cell_type=cell_type))
        else:
            new_cells.append(cell)

    return evolve_notebook_cells(contents, new_cells)
