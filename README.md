
# jupyter_ascending

[![Build Status](https://travis-ci.org//jupyter_ascending.svg?branch=master)](https://travis-ci.org//jupyter_ascending)
[![codecov](https://codecov.io/gh//jupyter_ascending/branch/master/graph/badge.svg)](https://codecov.io/gh//jupyter_ascending)


Sync Jupyter Notebooks from any editor

![Jupyter Ascending](./media/simple_jupyter_ascending.gif)
## Installation

```
$ pip install jupyter_ascending
$ # It is possible you won't need to run the following commands on newer version of jupyter notebook,
$ # but it's recommended that you do anyway, because installing extensions is hard.
$ jupyter nbextension install --py --sys-prefix jupyter_ascending
$ jupyter nbextension     enable jupyter_ascending --sys-prefix --py
$ jupyter serverextension enable jupyter_ascending --sys-prefix --py
```

You can confirm it's installed by checking:
```
$ jupyter nbextension     list
$ jupyter serverextension list
```

## About

Jupyter Ascending syncs the state between a python script and a Jupyter notebook.

At the moment, it syncs between python scripts that end with `.synced.py` and Jupyter notebooks with names that end with `.synced.ipynb`.

To get a properly formatted `.synced.py` file, you should use `jupytext` to generate one. You can convert it to a Jupyter notebook with `jupytext` as well!

## Getting started

Jupyter ascending provides some scripts to help users. To get a pair of synced py and ipynb files, you could run the following:

```
$ python -m jupyter_ascending.scripts.make_pair --base examples/test
```

Which will create a pair of files: `examples/test.synced.py` and `examples/test.synced.ipynb`. You can read the help for the command to find more information.

## Usage in Vim

To use in vim, see: [jupyter_ascending.vim](https://github.com/untitled-ai/jupyter_ascending.vim)


## Local development

To do local development:

```
# install dependencies
$ poetry install

# Installs the extension, using symlinks
$ jupyter nbextension install --py --sys-prefix --symlink jupyter_ascending

# Enables them, so it auto loads
$ jupyter nbextension enable jupyter_ascending --py --sys-prefix
$ jupyter serverextension enable jupyter_ascending --sys-prefix --py
```

To check that they are enabled, do something like this:

```
$ jupyter nbextension list
Known nbextensions:
  config dir: /home/tj/.pyenv/versions/3.8.1/envs/general/etc/jupyter/nbconfig
    notebook section
      jupytext/index  enabled
      - Validating: OK
      jupyter-js-widgets/extension  enabled
      - Validating: OK
      jupyter_ascending/extension  enabled
      - Validating: OK

$ jupyter serverextension list
config dir: /home/tj/.pyenv/versions/3.8.1/envs/general/etc/jupyter
    jupytext  enabled
    - Validating...
      jupytext 1.8.0 OK
    jupyter_ascending  enabled
    - Validating...
      jupyter_ascending 0.1.13 OK
```
