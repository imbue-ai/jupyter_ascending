# PyCharm Integration

You'll want to set PyCharm up so that it runs `jupyter_ascending.requests.sync` every time you save a `.sync.py` file. This can be done with a File Watcher (preferences->file watcher).

![File watcher config](../media/filewatcher.png)

For easy copying:
- Program: `$PyInterpreterDirectory$/python`
- Arguments: `-m jupyter_ascending.requests.sync --filename $FilePath$`

You'll need to make a custom file watcher scope: `file:*.sync.py`

Then, if you want to set a keyboard shortcut in PyCharm for "run cell" in the notebook (handy if you have the editor and notebook windows side by side), you can do it by setting up an External Tool (preferences->external tools).

![External tool config](../media/external_tool.png)

For easy copying:

- Program: `$PyInterpreterDirectory$/python`
- Arguments: `-m jupyter_ascending.requests.execute --filename $FilePath$ --linenumber $LineNumber$`
- Working Directory: `$ProjectFileDir$`


You'll want to set up a keyboard shortcut for this external tool in the keyboard shortcuts menu.

