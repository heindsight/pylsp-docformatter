import os

import pytest

from pylsp_docformatter import util


@pytest.fixture
def initial_wd(tmp_path):
    pth = tmp_path / "initial"
    pth.mkdir()
    return pth


@pytest.fixture
def target_wd(tmp_path):
    pth = tmp_path / "target"
    pth.mkdir()
    return pth


def test_tmp_workdir(initial_wd, target_wd):
    os.chdir(initial_wd)

    with util.temp_work_dir(target_wd):
        assert os.getcwd() == str(target_wd)

    assert os.getcwd() == str(initial_wd)
