import attr

from jupyter_ascending.notebook.data_types import JupyterCell
from jupyter_ascending.notebook.data_types import NotebookContents
from jupyter_ascending.notebook.evolve import evolve_cell_source
from jupyter_ascending.notebook.evolve import evolve_cell_type
from jupyter_ascending.notebook.evolve import evolve_notebook_cells
from jupyter_ascending.notebook.merge import OpCodes
from jupyter_ascending.notebook.merge import opcode_merge_cell_contents

SIMPLE_CONTENTS = NotebookContents(cells=[JupyterCell(cell_type="code", index=0, source=["x = 1; x"], output=["1"])])

THREE_CELL_CONTENTS = NotebookContents(
    cells=[
        JupyterCell(cell_type="code", index=0, source=["x = 1; x"], output=["1"]),
        JupyterCell(cell_type="code", index=1, source=["y = 2; y"], output=["2"]),
        JupyterCell(cell_type="code", index=2, source=["z = 3; z"], output=["3"]),
    ]
)


def _insert_notebook_cell(notebook: NotebookContents, new_cell: JupyterCell) -> NotebookContents:
    # TODO: Should this be moved somewhere?
    original_cells = notebook.cells

    new_cells = []
    for cell in original_cells:
        if cell.index < new_cell.index:
            new_cells.append(cell)
        else:
            if new_cell not in new_cells:
                new_cells.append(new_cell)

            new_cells.append(attr.evolve(cell, index=cell.index + 1))

    return evolve_notebook_cells(notebook, new_cells)


def test_passing_same_contents_means_same_output():
    opcodes = opcode_merge_cell_contents(SIMPLE_CONTENTS, SIMPLE_CONTENTS)

    assert len(opcodes) == 1
    assert opcodes[0].op_code == OpCodes.EQUAL


def test_change_one_value():
    new_contents = evolve_cell_source(SIMPLE_CONTENTS, 0, ["x = 2; x"])
    opcodes = opcode_merge_cell_contents(SIMPLE_CONTENTS, new_contents)

    assert len(opcodes) == 1
    assert opcodes[0].op_code == OpCodes.REPLACE


def test_change_one_of_multiple_values():
    new_contents = evolve_cell_source(THREE_CELL_CONTENTS, 0, ["x = 4; x"])

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)

    assert len(opcodes) == 2
    assert opcodes[0].op_code == OpCodes.REPLACE
    assert opcodes[1].op_code == OpCodes.EQUAL


def test_reorder_multiple_values():
    first_cell = attr.evolve(THREE_CELL_CONTENTS.cells[1], index=0, output=None)
    second_cell = attr.evolve(THREE_CELL_CONTENTS.cells[0], index=1, output=None)

    new_contents = NotebookContents(cells=[first_cell, second_cell, THREE_CELL_CONTENTS.cells[2]])
    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)
    assert len(opcodes) == 5

    assert [x.op_code for x in opcodes] == [
        OpCodes.INSERT,
        OpCodes.EQUAL,
        OpCodes.DELETE,
        OpCodes.EQUAL,
        OpCodes.COPY_OUTPUT,
    ]

    assert opcodes[-1].current_final_idx == 1
    assert opcodes[-1].updated_final_idx == 0


def test_remove_one_cell():
    # Notice that there isn't [2], and the output is removed
    cells_with_one_removed = [
        attr.evolve(THREE_CELL_CONTENTS.cells[0], output=None),
        attr.evolve(THREE_CELL_CONTENTS.cells[1], output=None),
    ]
    new_contents = NotebookContents(cells=cells_with_one_removed)

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)

    assert len(opcodes) == 2
    assert [x.op_code for x in opcodes] == [OpCodes.EQUAL, OpCodes.DELETE]

    assert opcodes[0].current_start_idx == 0
    assert opcodes[0].current_final_idx == 2
    assert opcodes[0].updated_start_idx == 0
    assert opcodes[0].updated_final_idx == 2


def test_remove_one_cell_beginning():
    # Notice that there isn't [0], and the output is removed
    cells_with_one_removed = [
        attr.evolve(THREE_CELL_CONTENTS.cells[1], output=None, index=0),
        attr.evolve(THREE_CELL_CONTENTS.cells[2], output=None, index=1),
    ]
    new_contents = NotebookContents(cells=cells_with_one_removed)

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)
    assert len(opcodes) == 2
    assert [x.op_code for x in opcodes] == [OpCodes.DELETE, OpCodes.EQUAL]

    assert opcodes[0].current == (0, 1)
    assert opcodes[1].current == (1, 3)


def test_remove_one_cell_and_update_another():
    # Updated source for index=1
    modified_source = ["y = 3; y"]

    cells_with_one_removed = [
        attr.evolve(THREE_CELL_CONTENTS.cells[0], output=None, index=0),
        attr.evolve(THREE_CELL_CONTENTS.cells[1], source=modified_source, output=None, index=1),
    ]
    new_contents = NotebookContents(cells=cells_with_one_removed)

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)
    assert [x.op_code for x in opcodes] == [OpCodes.EQUAL, OpCodes.REPLACE]

    assert opcodes[0].current == (0, 1)
    assert opcodes[0].updated == (0, 1)

    # Note: The replace takes the two cells and then replaces down to only one
    assert opcodes[1].current == (1, 3)
    assert opcodes[1].updated == (1, 2)


def test_insert_a_new_cell():
    inserted_cell = JupyterCell(cell_type="code", index=2, source=["print('hello world')"], output=None)
    new_contents = _insert_notebook_cell(THREE_CELL_CONTENTS, inserted_cell)

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)
    assert [x.op_code for x in opcodes] == [OpCodes.EQUAL, OpCodes.INSERT, OpCodes.EQUAL]

    assert opcodes[1].current == (2, 2)
    assert opcodes[1].updated == (2, 3)


def test_insert_a_new_cell_and_update_another():
    modified_source = ["y = 3; y"]
    inserted_cell = JupyterCell(cell_type="code", index=2, source=["print('hello world')"], output=None)

    new_contents = evolve_cell_source(_insert_notebook_cell(THREE_CELL_CONTENTS, inserted_cell), 1, modified_source)

    opcodes = opcode_merge_cell_contents(THREE_CELL_CONTENTS, new_contents)
    assert [x.op_code for x in opcodes] == [
        OpCodes.EQUAL,
        OpCodes.REPLACE,
        OpCodes.EQUAL,
    ]

    assert opcodes[1].current == (1, 2)
    assert opcodes[1].updated == (1, 3)


def test_changing_cell_type_sends_replace():
    new_contents = evolve_cell_type(SIMPLE_CONTENTS, 0, "markdown")
    opcodes = opcode_merge_cell_contents(SIMPLE_CONTENTS, new_contents)

    assert new_contents != SIMPLE_CONTENTS
    assert len(opcodes) == 1
    assert opcodes[0].op_code == OpCodes.REPLACE
