import pytest

from jupyter_ascending._environment import SYNC_EXTENSION
from jupyter_ascending.errors import UnableToFindNotebookException
from jupyter_ascending.handlers.server_extension import _clear_registered_servers
from jupyter_ascending.handlers.server_extension import _make_url
from jupyter_ascending.handlers.server_extension import get_server_for_notebook
from jupyter_ascending.handlers.server_extension import register_notebook_server


class TestGetSever:
    def setup_method(self, _method):
        _clear_registered_servers()

    @pytest.mark.asyncio
    async def test_clear_registered_servers(self):
        notebook_name = f"hello.{SYNC_EXTENSION}.ipynb"
        await register_notebook_server(notebook_name, 1234)
        assert get_server_for_notebook(notebook_name) is not None

        _clear_registered_servers()
        with pytest.raises(UnableToFindNotebookException):
            get_server_for_notebook(notebook_name)

    @pytest.mark.asyncio
    async def test_exact_match(self):
        notebook_name = f"hello.{SYNC_EXTENSION}.ipynb"
        notebook_port = 1234

        await register_notebook_server(notebook_name, notebook_port)
        assert get_server_for_notebook(notebook_name) == _make_url(notebook_port)

    @pytest.mark.asyncio
    async def test_stem_match(self):
        true_notebook_name = f"/home/tj/git/notebook.{SYNC_EXTENSION}.ipynb"
        remote_notebook_name = f"/home/other/git/notebook.{SYNC_EXTENSION}.ipynb"

        notebook_port = 1234

        await register_notebook_server(true_notebook_name, notebook_port)
        assert get_server_for_notebook(true_notebook_name) == _make_url(notebook_port)
        assert get_server_for_notebook(remote_notebook_name) == _make_url(notebook_port)

    @pytest.mark.asyncio
    async def test_more_than_stem_match(self):
        true_notebook_name = f"/home/tj/git/notebook.{SYNC_EXTENSION}.ipynb"
        do_not_pick_notebook = f"/home/tj/do_not_pick/notebook.{SYNC_EXTENSION}.ipynb"
        remote_notebook_name = f"/home/other/git/notebook.{SYNC_EXTENSION}.ipynb"

        notebook_port = 1234
        do_not_pick_port = 4444

        await register_notebook_server(true_notebook_name, notebook_port)
        await register_notebook_server(do_not_pick_notebook, do_not_pick_port)

        assert get_server_for_notebook(true_notebook_name) == _make_url(notebook_port)
        assert get_server_for_notebook(remote_notebook_name) == _make_url(notebook_port)

    @pytest.mark.asyncio
    async def test_equally_matching_stem_errors(self):
        foo_notebook_name = f"/home/foo/git/notebook.{SYNC_EXTENSION}.ipynb"
        bar_notebook_name = f"/home/bar/git/notebook.{SYNC_EXTENSION}.ipynb"

        foo_port = 1234
        bar_port = 4321

        current_notebook_name = f"/home/tj/git/notebook.{SYNC_EXTENSION}.ipynb"

        await register_notebook_server(foo_notebook_name, foo_port)
        await register_notebook_server(bar_notebook_name, bar_port)

        assert get_server_for_notebook(foo_notebook_name) == _make_url(foo_port)
        assert get_server_for_notebook(bar_notebook_name) == _make_url(bar_port)

        # Can't determine what this server
        with pytest.raises(UnableToFindNotebookException):
            get_server_for_notebook(current_notebook_name)

    @pytest.mark.asyncio
    async def test_no_matches(self):
        loaded_notebook_name = f"/home/tj/notebook.{SYNC_EXTENSION}.ipynb"
        not_loaded_notebook_name = f"/home/tj/other.{SYNC_EXTENSION}.ipynb"

        await register_notebook_server(loaded_notebook_name, 1234)

        with pytest.raises(UnableToFindNotebookException):
            get_server_for_notebook(not_loaded_notebook_name)
