"""Miscelaneous utility functions."""

import contextlib
import os
import pathlib
from typing import Generator


@contextlib.contextmanager
def temp_work_dir(workdir: pathlib.Path) -> Generator[None, None, None]:
    """Temporarily change working directory."""
    initial_workdir = os.getcwd()
    os.chdir(workdir)

    try:
        yield
    finally:
        os.chdir(initial_workdir)
