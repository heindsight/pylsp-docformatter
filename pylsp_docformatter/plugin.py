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

from .types import FormatResult, LspSettings, Range
from .util import temp_work_dir


logger = logging.getLogger(__name__)


@hookimpl
def pylsp_settings() -> LspSettings:
    """Get default plugin settings."""
    logger.info("Initializing pylsp_docformatter")

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
) -> List[FormatResult]:
    """Format an entire document."""
    docformat_config = load_docformat_config(workspace, config, document)
    return _do_format(docformat_config, document)


@hookimpl(trylast=True)
def pylsp_format_range(
    config: Config, workspace: Workspace, document: Document, range: Range
) -> List[FormatResult]:
    """Format a range of lines."""
    docformat_config = load_docformat_config(workspace, config, document)
    range["start"]["character"] = 0
    range["end"]["character"] = 0
    return _do_format(docformat_config, document, range)


def _do_format(
    config: docformatter.Configurater, document: Document, range: Optional[Range] = None
) -> List[FormatResult]:
    if range:
        text = "".join(document.lines[range["start"]["line"] : range["end"]["line"]])
    else:
        range = {
            "start": {"line": 0, "character": 0},
            "end": {"line": len(document.lines), "character": 0},
        }
        text = document.source

    stdout = io.StringIO(newline="")
    stderr = io.StringIO(newline="")

    formatter = docformatter.Formatter(
        config.args,
        stdin=io.StringIO(text, newline=""),
        stdout=stdout,
        stderror=stderr,
    )

    formatter.do_format_standard_in(config.parser)

    formatted_text = stdout.getvalue()

    return [{"range": range, "newText": formatted_text}]


def load_docformat_config(
    workspace: Workspace, config: Config, document: Document
) -> docformatter.Configurater:
    """Load docformatter configuration for an LSP workspace."""
    plugin_settings = config.plugin_settings(
        "pylsp_docformatter", document_path=document.path
    )
    config_file = plugin_settings.get("config_file")

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

    return configurater
