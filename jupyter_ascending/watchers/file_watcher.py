import time

import ipywidgets as widgets
import jupytext
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler

from jupyter_ascending.sync import make_comm
from jupyter_ascending.sync import update_cell_contents


class NotebookEventHandler(FileSystemEventHandler):
    actual_notebook_name: str
    status_notebook_name: str

    display_widget: widgets.Text

    def __init__(self, notebook_name: str, display_widget: widgets.Text):
        super().__init__()

        assert ".status.py" in notebook_name, "Must be a status notebook that you're editing"

        self.status_notebook_name = notebook_name
        self.actual_notebook_name = notebook_name.replace(".status.py", ".ipynb")

        self.display_widget = display_widget

    def on_modified(self, event: FileSystemEvent):
        # Skip directories -- just want the file
        if event.is_directory:
            return

        if event.src_path != self.status_notebook_name:
            return

        self.display_widget.value = f"{time.time()}: synced"

        with open(event.src_path, "r") as reader:
            raw_result = reader.read()

        result = jupytext.reads(raw_result, fmt="py:percent")

        # Use comm to send a message from the kernel
        my_comm = make_comm(self.actual_notebook_name)
        update_cell_contents(my_comm, result)
