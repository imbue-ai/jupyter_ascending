#!/usr/bin/env python
# coding: utf-8

# Copyright (c) tjdevries.
# Distributed under the terms of the Modified BSD License.

"""
TODO: Add module docstring
"""

from IPython.core.magic import Magics
from IPython.core.magic import line_magic
from IPython.core.magic import magics_class
from ipywidgets import DOMWidget
from traitlets import Unicode

from jupyter_ascending._frontend import module_name
from jupyter_ascending._frontend import module_version


class SyncWidget(DOMWidget):
    """
    Widget responsible for syncing the state from your preferred file to the editor
    """

    _model_name = Unicode("ExampleModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode("ExampleView").tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    value = Unicode("Waiting to sync...").tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@magics_class
class SyncMagic(Magics):
    @line_magic
    def start_notebook_syncing(self, line):
        return SyncWidget()
