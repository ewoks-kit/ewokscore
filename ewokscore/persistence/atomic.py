import os
import string
import random
from contextlib import contextmanager
from typing import Union, Tuple
from silx.io import h5py_utils


def random_string(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def nonexisting_tmp_file(filename):
    tmpname = filename + ".tmp" + random_string(6)
    while os.path.exists(tmpname):
        tmpname = filename + ".tmp" + random_string(6)
    return tmpname


def mkdir(filename):
    dirname = os.path.dirname(filename)
    if dirname:
        os.makedirs(dirname, exist_ok=True)


@contextmanager
def atomic_file(filename):
    filename = str(filename)
    tmpname = nonexisting_tmp_file(filename)
    mkdir(tmpname)
    try:
        yield tmpname
    except Exception:
        try:
            os.unlink(tmpname)
        except FileNotFoundError:
            pass
        raise
    os.rename(tmpname, filename)


@contextmanager
def atomic_write(filename):
    with atomic_file(filename) as tmpname:
        with open(tmpname, mode="w") as f:
            yield f


@h5py_utils.retry_contextmanager()
def append_hdf5(filename):
    with h5py_utils.File(filename, mode="a") as h5file:
        yield h5file


@contextmanager
def atomic_hdf5(
    filename, h5group: Union[None, str]
) -> Tuple[h5py_utils.File, Union[None, str]]:
    if not h5group or h5group == "/":
        with atomic_file(filename) as tmpname:
            with h5py_utils.File(tmpname, mode="a") as f:
                yield f, h5group
    else:
        # Atomic because an HDF5 file can be modified
        # by only one process at a time
        with append_hdf5(filename, retry_period=1, retry_timeout=360) as h5file:
            yield h5file, h5group
