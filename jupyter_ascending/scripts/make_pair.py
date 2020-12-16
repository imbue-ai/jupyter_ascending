import argparse
from pathlib import Path

import jupytext

_STARTER_CONTENTS = """# ---
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

# %%
print("Hello, world!")

"""


def create_new_file(base: str, force: bool):
    assert not base.endswith(".py"), "base: Cannot end with '.py'"
    assert not base.endswith(".synced.py"), "base: Cannot end with 'synced.py' -- we're adding that!"
    assert not base.endswith(".ipynb"), "base: Cannot end with '.ipynb'"
    assert not base.endswith(".synced.ipynb"), "base: Cannot end with '.ipynb' -- we're adding that!"
    assert not base.endswith(".synced"), "we're going to add '.synced'"

    py_path = base + ".synced.py"
    ipynb_path = base + ".synced.ipynb"

    if not force and Path(py_path).exists():
        print(f"Path '{py_path}' already exists. Call with --force to override.")
        return

    if not force and Path(ipynb_path).exists():
        print(f"Path '{ipynb_path}' already exists. Call with --force to override.")
        return

    with open(py_path, "w") as f:
        print("Writing :", py_path)
        f.write(_STARTER_CONTENTS)

    print("Writing :", ipynb_path)
    jupytext.write(jupytext.reads(_STARTER_CONTENTS, "py:percent"), ipynb_path)
    # with open(ipynb_path, "w") as f:

    print("Success!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Base filename to add (do not include .py or .ipynb)", required=True)
    parser.add_argument("-f", "--force", help="Override existing files if passed.", default=False, action="store_true")

    arguments = parser.parse_args()
    create_new_file(arguments.base, arguments.force)
