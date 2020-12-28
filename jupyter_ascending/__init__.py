#!/usr/bin/env python
# coding: utf-8

# Copyright (c) tjdevries.
# Distributed under the terms of the Modified BSD License.

from jupyter_ascending._version import __version__
from jupyter_ascending._version import version_info
from jupyter_ascending.extension import load_ipython_extension
from jupyter_ascending.extension import load_jupyter_server_extension
from jupyter_ascending.nbextension import _jupyter_nbextension_paths


def _jupyter_server_extension_paths():
    return [{
        "module": "jupyter_ascending",
    }]


__all__ = [
    "__version__",
    "_jupyter_nbextension_paths",
    "load_ipython_extension",
    "_jupyter_server_extension_paths",
    "load_jupyter_server_extension",
    "version_info",
]
