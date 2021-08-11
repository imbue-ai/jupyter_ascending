# Visual Studio Code Integration

Note: this will only work if you have a project folder open - it won't work if you just have an individual file open.

- Make sure you have the Python extension installed and have selected a python interpreter (from the command pallete (ctrl-shift-p) -> python interpreter) that has jupyter_ascending installed.
- Create Tasks in `.vscode/tasks.json` following the example in this repo's `.vscode/tasks.json`. You'll probably want one task for "sync code to notebook" and another for "execute cell", as we have in the example. If you don't already have Tasks set up, you can just copy our example file into your project. Otherwise just add our tasks alongside your existing ones in that file.
- Create shortcuts for the tasks in your `keybindings.json` file. You can access this file by opening the keyboard shortcuts pane (preferences -> keyboard shortcuts), and then hitting the little button in the upper right corner labeled Open Keyboard Shortcuts (JSON). Then add entries like the following, where `args` matches the Task's `label`:
```json
[
    {
        "key": "shift+enter",
        "command": "workbench.action.tasks.runTask",
        "args": "Jupyter Ascending Run Cell"
      },
      {
        "key": "alt+s",
        "command": "workbench.action.tasks.runTask",
        "args": "Jupyter Ascending Sync"
      }
]
```

Then everything should work properly! If you see error messages, open the Terminal (View -> Terminal) and run the Task again to see the command output. It should also have the path to the full log file with more detailed logs.

If you'd like to auto-sync on file save, you can try an extension like [Trigger Task on Save](https://marketplace.visualstudio.com/items?itemName=Gruntfuggly.triggertaskonsave), with a file filter to only sync `.sync.py` files.


Things we'd like help improving:
- The terminal always gets opened when running a task, even with "presentation":"reveal":"never" set in the Task. This seems to be due to an issue with the VSCode Python extension (see [here](https://github.com/microsoft/vscode/issues/65179)). Just making the window small is probably the best workaround for now.
