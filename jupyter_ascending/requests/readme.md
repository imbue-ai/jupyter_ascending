Contains the Python client library for Jupyter ascending.

The available commands are:

`execute`: run a single cell

`execute_all`: run all cells

`get_status`: idk?

`sync`: make the remote notebook match like the local `.sync.py` file

Typical usage is to do something like 

`python -m jupyter_ascending.requests.execute --filename $FilePath$ --linenumber $LineNumber$`


How this works is that the client library sends the command using RPC to the Jupyter Ascending JSON-RPC server running alongside the jupyter server. Then that server forwards the command along to a second JSON-RPC server running alongside the actual notebook that this file is matched to.