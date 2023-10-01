from textwrap import dedent
from unittest.mock import Mock

import pytest
from pylsp import uris
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

from pylsp_docformatter import plugin


@pytest.fixture
def root_path(tmp_path):
    pth = tmp_path / "project_root"
    pth.mkdir()
    return pth


@pytest.fixture
def src_path(root_path):
    pth = root_path / "src"
    pth.mkdir()
    return pth


@pytest.fixture
def root_uri(root_path):
    return uris.from_fs_path(str(root_path))


@pytest.fixture
def config(root_uri):
    """Return a config object."""
    return Config(root_uri, {}, 0, {})


@pytest.fixture
def workspace(root_uri, config):
    """Return a workspace."""
    return Workspace(root_uri, Mock(), config)


@pytest.fixture
def doc_lines():
    return [
        '"""Simple example for testing."""',
        "",
        "",
        "def main():",
        '    print("Hello World!")',
        "",
    ]


@pytest.fixture
def newline():
    return "\n"


@pytest.fixture
def doc_content(doc_lines, newline):
    return newline.join(doc_lines)


@pytest.fixture
def document(workspace, src_path, doc_content):
    dest_path = src_path / "example.py"
    dest_path.write_text(doc_content)
    document_uri = uris.from_fs_path(str(dest_path))
    return Document(document_uri, workspace, source=doc_content)


class TestLoadDocformatConfig:
    @pytest.fixture
    def pyproject_toml(self, root_path):
        config = """\
            [tool.docformatter]
            black = true
            """

        pth = root_path / "pyproject.toml"
        pth.write_text(dedent(config))
        return pth

    @pytest.fixture
    def config_file(self, tmp_path):
        config = """\
            [docformatter]
            wrap-summaries = 42
            """
        pth = tmp_path / "setup.cfg"
        pth.write_text(dedent(config))
        return pth

    def test_default_plugin_settings(self, pyproject_toml, config, workspace):
        configurater = plugin.load_docformat_config(config, workspace)

        assert configurater.args.black

    def test_with_config_file(self, config_file, config, workspace):
        config._plugin_settings = {
            "plugins": {
                "docformatter": {
                    "enabled": True,
                    "config_file": str(config_file),
                }
            }
        }
        configurater = plugin.load_docformat_config(config, workspace)

        assert configurater.args.wrap_summaries == 42


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_formats_document(config, workspace, newline, document, doc_content):
    result = plugin.pylsp_format_document(
        config=config, workspace=workspace, document=document
    )

    assert result == [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 5, "character": 0},
            },
            "newText": doc_content,
        }
    ]


def test_formats_range(
    config,
    workspace,
    document,
    doc_content,
):
    result = plugin.pylsp_format_range(
        config=config,
        workspace=workspace,
        document=document,
        range={
            "start": {"line": 0, "character": 2},
            "end": {"line": 1, "character": 5},
        },
    )

    assert result == [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 2, "character": 0},
            },
            "newText": '"""Simple example for testing."""\n\n',
        }
    ]
