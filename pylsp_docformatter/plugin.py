import io
import logging
from functools import lru_cache
from typing import List, Optional

import docformatter
from pylsp import hookimpl
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

from .types import FormatResult, Range
from .util import temp_work_dir


logger = logging.getLogger(__name__)


@hookimpl
def pylsp_settings():
    logger.info("Initializing pylsp_docformatter")

    return {
        "plugins": {
            "docformatter": {
                "enabled": True,
            }
        }
    }


@hookimpl(trylast=True)
def pylsp_format_document(
    config: Config, workspace: Workspace, document: Document
) -> List[FormatResult]:
    docformat_config = load_docformat_config(config, workspace)
    return do_format(docformat_config, document)


@hookimpl(trylast=True)
def pylsp_format_range(
    config: Config, workspace: Workspace, document: Document, range: Range
) -> List[FormatResult]:
    docformat_config = load_docformat_config(config, workspace)
    range["start"]["character"] = 0
    range["end"]["line"] += 1
    range["end"]["character"] = 0
    return do_format(docformat_config, document, range)


def do_format(
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


@lru_cache
def load_docformat_config(
    config: Config, workspace: Workspace
) -> docformatter.Configurater:
    plugin_settings = config.plugin_settings("docformatter")
    config_file = plugin_settings.get("config_file")

    args = ["docformatter"]
    if config_file:
        args.extend(["--config", config_file])

    args.append("-")

    with temp_work_dir(workspace.root_path):
        configurater = docformatter.Configurater(args)
        configurater.do_parse_arguments()

    return configurater
