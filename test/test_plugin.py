from pathlib import Path
from textwrap import dedent
from typing import List
from unittest.mock import Mock

import pytest
from pylsp import uris
from pylsp.config.config import Config
from pylsp.workspace import Document, Workspace

from pylsp_docformatter import plugin


@pytest.fixture
def root_path(tmp_path: Path) -> Path:
    pth = tmp_path / "project_root"
    pth.mkdir()
    return pth


@pytest.fixture
def src_path(root_path: Path) -> Path:
    pth = root_path / "src"
    pth.mkdir()
    return pth


@pytest.fixture
def root_uri(root_path: Path) -> str:
    return uris.from_fs_path(str(root_path))


@pytest.fixture
def config(root_uri: str) -> Config:
    """Return a config object."""
    return Config(root_uri, {}, 0, {})


@pytest.fixture
def workspace(root_uri: str, config: Config) -> Workspace:
    """Return a workspace."""
    return Workspace(root_uri, Mock(), config)


@pytest.fixture
def doc_lines() -> List[str]:
    return [
        '"""Simple example for testing."""',
        "",
        "",
        "def main():",
        '    print("Hello World!")',
        "",
    ]


@pytest.fixture
def newline() -> str:
    return "\n"


@pytest.fixture
def doc_content(doc_lines: List[str], newline: str) -> str:
    return newline.join(doc_lines)


@pytest.fixture
def document(workspace: Workspace, src_path: Path, doc_content: str) -> Document:
    dest_path = src_path / "example.py"
    dest_path.write_text(doc_content)
    document_uri = uris.from_fs_path(str(dest_path))
    return Document(document_uri, workspace, source=doc_content)


class TestLoadDocformatConfig:
    @pytest.fixture
    def pyproject_toml(self, root_path: Path) -> Path:
        config = """\
            [tool.docformatter]
            black = true
            """

        pth = root_path / "pyproject.toml"
        pth.write_text(dedent(config))
        return pth

    @pytest.fixture
    def config_file(self, tmp_path: Path) -> Path:
        config = """\
            [docformatter]
            wrap-summaries = 42
            """
        pth = tmp_path / "setup.cfg"
        pth.write_text(dedent(config))
        return pth

    @pytest.fixture
    def same_workspace_doc(self, workspace: Workspace, src_path: Path) -> Document:
        text = "print('hello')\n"
        dest_path = src_path / "example_2.py"
        dest_path.write_text(text)
        document_uri = uris.from_fs_path(str(dest_path))
        return Document(document_uri, workspace, source=text)

    @pytest.fixture
    def other_project_root(self, tmp_path: Path) -> Path:
        pth = tmp_path / "other_project"
        pth.mkdir()
        return pth

    @pytest.fixture
    def other_config(self, other_project_root: Path) -> Config:
        root_uri = uris.from_fs_path(str(other_project_root))
        return Config(root_uri, {}, 0, {})

    @pytest.fixture
    def other_workspace(
        self, other_project_root: Path, other_config: Config
    ) -> Workspace:
        root_uri = uris.from_fs_path(str(other_project_root))
        return Workspace(root_uri, Mock(), other_config)

    @pytest.fixture
    def other_workspace_doc(
        self, other_project_root: Path, other_workspace: Workspace
    ) -> Document:
        text = "print('hello')\n"

        doc_path = other_project_root / "example.py"
        doc_path.write_text(text)
        document_uri = uris.from_fs_path(str(doc_path))

        return Document(document_uri, other_workspace, source=text)

    @pytest.mark.usefixtures("pyproject_toml")
    def test_default_plugin_settings(
        self, config: Config, workspace: Workspace, document: Document
    ) -> None:
        configurater = plugin.load_docformat_config(workspace, config, document)

        assert configurater.args.black

    def test_with_config_file(
        self,
        config: Config,
        workspace: Workspace,
        config_file: Path,
        document: Document,
    ) -> None:
        config._plugin_settings = {
            "plugins": {
                "pylsp_docformatter": {
                    "enabled": True,
                    "config_file": str(config_file),
                }
            }
        }
        configurater = plugin.load_docformat_config(workspace, config, document)

        assert configurater.args.wrap_summaries == 42

    def test_caches_config_same_workspace_root(
        self,
        config: Config,
        workspace: Workspace,
        document: Document,
        same_workspace_doc: Document,
    ):
        plugin._load_docformat_config.cache_clear()

        configurater1 = plugin.load_docformat_config(workspace, config, document)
        configurater2 = plugin.load_docformat_config(
            workspace, config, same_workspace_doc
        )

        assert configurater1 is configurater2

        cache_info = plugin._load_docformat_config.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 1

    def test_other_workspace_root_not_cached(
        self,
        config: Config,
        workspace: Workspace,
        document: Document,
        other_config: Config,
        other_workspace: Workspace,
        other_workspace_doc: Document,
    ):
        plugin._load_docformat_config.cache_clear()

        configurater1 = plugin.load_docformat_config(workspace, config, document)
        configurater2 = plugin.load_docformat_config(
            other_workspace, other_config, other_workspace_doc
        )

        assert configurater1 is not configurater2

        cache_info = plugin._load_docformat_config.cache_info()
        assert cache_info.misses == 2
        assert cache_info.hits == 0


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_formats_document(
    config: Config,
    workspace: Workspace,
    newline: str,
    document: Document,
    doc_content: str,
) -> None:
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
    config: Config,
    workspace: Workspace,
    document: Document,
    doc_content: str,
) -> None:
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
