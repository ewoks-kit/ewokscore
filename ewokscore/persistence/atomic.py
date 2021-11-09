import os
import string
import random
from pathlib import Path
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple
from silx.io import h5py_utils


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def nonexisting_tmp_file(path: Path) -> Path:
    tmppath = path.with_name(f"tmp_ewoks_{random_string(6)}_{path.name}")
    while tmppath.exists():
        tmppath = path.with_name(f"tmp_ewoks_{random_string(6)}_{path.name}")
    return tmppath


@contextmanager
def atomic_create_path(path: Path) -> Iterable[Path]:
    """Yields a temporary path which will be renamed to the requested path
    or deleted on failure.
    """
    tmppath = nonexisting_tmp_file(path)
    tmppath.parent.mkdir(parents=True, exist_ok=True)
    try:
        yield tmppath
    except Exception:
        try:
            os.unlink(tmppath)
        except FileNotFoundError:
            pass
        raise
    tmppath.rename(path)  # overwrite when it exists


@contextmanager
def atomic_write(path: Path, **kw):
    with atomic_create_path(path) as tmpname:
        with open(tmpname, mode="w", **kw) as f:
            yield f


@h5py_utils.retry_contextmanager()
def append_hdf5(filename, **kw):
    with h5py_utils.File(filename, mode="a", **kw) as h5file:
        yield h5file


@contextmanager
def atomic_write_hdf5(
    path, h5group: Optional[str], **kw
) -> Tuple[h5py_utils.File, Optional[str]]:
    if not h5group or h5group == "/":
        with atomic_create_path(path) as tmppath:
            with h5py_utils.File(tmppath, mode="a", **kw) as f:
                yield f, h5group
    else:
        with append_hdf5(path, retry_period=0.5, retry_timeout=360, **kw) as f:
            yield f, h5group
