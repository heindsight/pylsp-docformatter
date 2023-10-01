import contextlib
import os
import pathlib
from typing import Iterator


@contextlib.contextmanager
def temp_work_dir(workdir: pathlib.Path) -> Iterator[None]:
    """Temporarily change working directory to `workdir`"""
    initial_workdir = os.getcwd()
    os.chdir(workdir)

    try:
        yield
    finally:
        os.chdir(initial_workdir)
