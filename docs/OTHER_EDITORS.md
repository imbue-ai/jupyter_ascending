# Integrating Other Editors

To use Jupyter Ascending in a different editor, you just need to be able to set up a few hooks:

On file save (only execute on files with extension `.sync.py`):

`python -m jupyter_ascending.requests.sync --filename [file_path]`

Then you can map keyboard shortcuts to:


Run cell:

`python jupyter_ascending.requests.execute --filename [file_path] --linenumber [line_number]`

The execution commands (run cell / run all cells) will sync the file before running the code, so you just need to make sure that the file is saved in order to run the current version of the code in your editor.


If you get this working in a new editor, we'd love if you would show us how you set it up!
