"""PyLSP plugin to format docstrings using docformatter."""

import difflib
import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import Generator, List, Optional

import docformatter
from pylsp import hookimpl, text_edit
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

from .types import LspSettings, Range, TextEdit
from .util import temp_work_dir


logger = logging.getLogger(__name__)


@hookimpl
def pylsp_settings() -> LspSettings:
    """Get default plugin settings."""
    logger.info("Initializing pylsp_docformatter config")

    return {
        "plugins": {
            "pylsp_docformatter": {
                "enabled": True,
            }
        }
    }


@hookimpl(wrapper=True)
def pylsp_format_document(
    config: Config, workspace: Workspace, document: Document
) -> Generator[None, List[TextEdit], List[TextEdit]]:
    """Format an entire document."""
    logger.debug("Formatting document %s", document.path)
    docformat_config = load_docformat_config(workspace, config, document)

    edits = yield

    if edits:
        text = text_edit.apply_text_edits(document, edits)
    else:
        text = document.source

    range_ = Range(
        start={"line": 0, "character": 0},
        end={"line": len(document.lines), "character": 0},
    )

    formatted_text = _do_format(docformat_config, text)

    return [{"range": range_, "newText": formatted_text}]


@hookimpl(wrapper=True)
def pylsp_format_range(
    config: Config, workspace: Workspace, document: Document, range: Range
) -> Generator[None, List[TextEdit], Optional[List[TextEdit]]]:
    """Format a range of lines."""
    logger.debug(
        "Formatting document %s, lines %s to %s",
        document.path,
        range["start"]["line"],
        range["end"]["line"],
    )

    docformat_config = load_docformat_config(workspace, config, document)

    edits = yield

    if edits:
        text = text_edit.apply_text_edits(document, edits)
        range = _adjust_range(range, edits)

    else:
        text = document.source

        range["start"]["character"] = 0

        if range["end"]["character"] != 0:
            # If the end character is not at the start of the line
            # we need to include the next line
            range["end"]["line"] += 1
            range["end"]["character"] = 0

    formatted_text = _do_format(docformat_config, text, range)

    return _get_changes(document, formatted_text)


def _do_format(
    config: docformatter.Configurater, text: str, range_: Optional[Range] = None
) -> str:
    if range_:
        # docformatter uses 1-based line numbers where both start and end are inclusive
        # LSP uses 0-based line numbers where start is inclusive and end is exclusive,
        # so we need to adjust the range accordingly
        config.args.line_range = (range_["start"]["line"] + 1, range_["end"]["line"])

    stdout = io.StringIO(newline="")
    stderr = io.StringIO(newline="")

    formatter = docformatter.Formatter(
        config.args,
        stdin=io.StringIO(text, newline=""),
        stdout=stdout,
        stderror=stderr,
    )

    formatter.do_format_standard_in(config.parser)

    return stdout.getvalue()


def _get_changes(document: Document, text: str) -> Optional[List[TextEdit]]:
    """Get the changes required to transform the document into the specified text."""
    if document.source == text:
        return None

    new_lines = text.splitlines(True)
    matcher = difflib.SequenceMatcher(None, document.lines, new_lines)

    old_start = -1
    old_end = -1

    edited_start = -1
    edited_end = -1

    for tag, orig_start, orig_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            continue

        if old_start == -1:
            old_start = orig_start
            edited_start = new_start

        old_end = orig_end
        edited_end = new_end

    text = "".join(new_lines[edited_start:edited_end])

    return [
        {
            "newText": text,
            "range": Range(
                start={"line": old_start, "character": 0},
                end={"line": old_end, "character": 0},
            ),
        }
    ]


def _adjust_range(range_: Range, edits: List[TextEdit]) -> Range:
    start = range_["start"].copy()
    lines = range_["end"]["line"] - range_["start"]["line"]

    for edit in edits:
        if edit["range"]["start"]["line"] < start["line"]:
            start["line"] = edit["range"]["start"]["line"]

        diff = (edit["range"]["end"]["line"] - edit["range"]["start"]["line"]) - len(
            edit["newText"].splitlines()
        )

        lines += diff

    return Range(
        start=start,
        end={"line": start["line"] + lines, "character": 0},
    )


def load_docformat_config(
    workspace: Workspace, config: Config, document: Document
) -> docformatter.Configurater:
    """Load docformatter configuration for an LSP workspace."""
    plugin_settings = config.plugin_settings(
        "pylsp_docformatter", document_path=document.path
    )
    config_file = plugin_settings.get("config_file")

    logger.info(
        "Loading docformatter config for workspace %s (config file %s)",
        workspace.root_path,
        config_file,
    )

    return _load_docformat_config(workspace.root_path, config_file)


@lru_cache
def _load_docformat_config(
    workspace_root: Path, config_file: Optional[str]
) -> docformatter.Configurater:
    """Load docformatter config from the workspace root directory."""
    args = ["docformatter"]

    if config_file:
        args.extend(["--config", config_file])

    args.append("-")

    with temp_work_dir(workspace_root):
        configurater = docformatter.Configurater(args)
        configurater.do_parse_arguments()

    logger.info("Loaded docformatter config: %s", vars(configurater.args))

    return configurater
