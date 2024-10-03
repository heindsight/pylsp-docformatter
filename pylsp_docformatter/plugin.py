"""PyLSP plugin to format docstrings using docformatter."""
import io
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import docformatter
from pylsp import hookimpl
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


@hookimpl(trylast=True)
def pylsp_format_document(
    config: Config, workspace: Workspace, document: Document
) -> List[TextEdit]:
    """Format an entire document."""
    logger.debug("Formatting document %s", document.path)
    docformat_config = load_docformat_config(workspace, config, document)
    return _do_format(docformat_config, document)


@hookimpl(trylast=True)
def pylsp_format_range(
    config: Config, workspace: Workspace, document: Document, range: Range
) -> List[TextEdit]:
    """Format a range of lines."""
    logger.debug(
        "Formatting document %s, lines %s to %s",
        document.path,
        range["start"]["line"],
        range["end"]["line"],
    )

    docformat_config = load_docformat_config(workspace, config, document)
    range["start"]["character"] = 0
    range["end"]["character"] = 0
    return _do_format(docformat_config, document, range)


def _do_format(
    config: docformatter.Configurater,
    document: Document,
    range_: Optional[Range] = None,
) -> List[TextEdit]:
    if range_:
        # docformatter uses 1-based line numbers where both start and end are inclusive
        # LSP uses 0-based line numbers where start is inclusive and end is exclusive,
        # so we need to adjust the range accordingly
        config.args.line_range = (range_["start"]["line"] + 1, range_["end"]["line"])

    stdout = io.StringIO(newline="")
    stderr = io.StringIO(newline="")

    formatter = docformatter.Formatter(
        config.args,
        stdin=io.StringIO(document.source, newline=""),
        stdout=stdout,
        stderror=stderr,
    )

    formatter.do_format_standard_in(config.parser)

    formatted_text = stdout.getvalue()

    formatted_range = _adjust_range(document, formatted_text, range_)
    formatted_text = _get_lines(formatted_text, formatted_range)

    return [{"range": formatted_range, "newText": formatted_text}]


def _adjust_range(document: Document, text: str, range_: Optional[Range]) -> Range:
    """Adjust the end of the range to account for changes in the text."""
    if range_ is None:
        return Range(
            start={"line": 0, "character": 0},
            end={"line": len(text.splitlines()), "character": 0},
        )

    line_diff = len(text.splitlines()) - len(document.lines)

    return Range(
        start={"line": range_["start"]["line"], "character": 0},
        end={
            "line": range_["end"]["line"] + line_diff,
            "character": 0,
        },
    )


def _get_lines(text: str, range_: Range) -> str:
    """Get the lines in the specified range."""
    lines = text.splitlines(True)

    return "".join(lines[range_["start"]["line"] : range_["end"]["line"]])


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
