import argparse
from functools import partial
from pathlib import Path
from typing import List

from loguru import logger

from jupyter_ascending.json_requests import ExecuteRequest
from jupyter_ascending.logger import setup_logger
from jupyter_ascending.requests.client_lib import request_notebook_command
from jupyter_ascending.requests.sync import send as sync_send
import jupytext

def _find_cell_number(lines: List[str], linenr: int) -> int:
  linenr = int(linenr)
  text = '\n'.join(lines)
  conv = jupytext.jupytext.TextNotebookConverter(jupytext.formats.divine_format(text), None)
  metadata, jupyter_md, header_cell, pos = jupytext.header.header_to_metadata_and_cell(
      lines,
      conv.implementation.header_prefix,
      conv.implementation.extension,
      conv.fmt.get(
          "root_level_metadata_as_raw_cell",
          conv.config.root_level_metadata_as_raw_cell
          if conv.config is not None
          else True,
      ),
  )
  conv.update_fmt_with_notebook_options(metadata, read=True)
  default_language = jupytext.languages.default_language_from_metadata_and_ext(
      metadata, conv.implementation.extension)

  lines = lines[pos:]

  cellnr = 0
  curpos = pos
  while lines:
    reader = conv.implementation.cell_reader_class(conv.fmt, default_language)
    cell, pos = reader.read(lines)
    curpos += pos
    lines = lines[pos:]
    if linenr < curpos:#curpos >= linenr:
      return cellnr
    cellnr += 1
  return -1


def send(file_name: str, line_number: int, *args, **kwargs):
    logger.debug("Starting execute request")

    # Always pass absolute path
    file_name = str(Path(file_name).absolute())

    request_obj = partial(ExecuteRequest, file_name=file_name, contents="")

    with open(file_name, "r") as reader:
        lines = reader.readlines()

    cell_index = _find_cell_number(lines, line_number)

    final_request = request_obj(cell_index=cell_index)
    logger.info(f"Sending request with {final_request}")
    request_notebook_command(final_request)
    logger.info("... Complete")


if __name__ == "__main__":
    setup_logger()
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", help="Filename to send")
    parser.add_argument("--linenumber", help="Line number that the cursor is currently on")

    arguments = parser.parse_args()

    # Sync code first
    sync_send(arguments.filename)
    send(arguments.filename, arguments.linenumber)
