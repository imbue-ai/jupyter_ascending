from jupyter_ascending.requests.execute import _find_cell_number


def test_find_cell_number():
    filetext = """# %%  # Line 1, Cell 0
print("Hello, world!")  # Line 2, Cell 0
# %%                    # Line 3, Cell 1
print("Goodby, world!") # Line 4, Cell 1
"""
    lines = filetext.splitlines()
    assert _find_cell_number(lines, 0) == 0
    assert _find_cell_number(lines, 1) == 0
    assert _find_cell_number(lines, 2) == 0
    assert _find_cell_number(lines, 3) == 1
    assert _find_cell_number(lines, 4) == 1


def test_find_cell_number_with_optional_yaml_header():
    filetext = """# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%                   # Line 15, Cell 0
print("Hello, world!") # Line 16, Cell 0
                       # Line 17, Cell 0
# %%                   # Line 18, Cell 1
print("Goodbye, ...")  # Line 19, Cell 1
                       # Line 20, Cell 1
print("world!")        # Line 21, Cell 1
                       # Line 22, Cell 1

"""
    lines = filetext.splitlines()
    assert _find_cell_number(lines, 0) == 0
    assert _find_cell_number(lines, 1) == 0
    assert _find_cell_number(lines, 14) == 0
    assert _find_cell_number(lines, 15) == 0
    assert _find_cell_number(lines, 16) == 0
    assert _find_cell_number(lines, 18) == 1
    assert _find_cell_number(lines, 21) == 1
    # Line 23 and 25 - blank line and beyond EOF.
    # Both return the last cell.
    assert _find_cell_number(lines, 23) == 1
    assert _find_cell_number(lines, 25) == 1
