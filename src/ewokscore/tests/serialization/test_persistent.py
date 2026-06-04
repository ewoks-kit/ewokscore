import json
import sys

from silx.io.dictdump import h5todict

from ...persistence.json import JsonProxy
from ...persistence.nexus import NexusProxy
from ...persistence.proxy import DataUri
from . import example_data
from .example_data import compare_hdf5
from .example_data import compare_json


def test_json_data_persistence(tmp_path):
    path = tmp_path / "data.json"
    if sys.platform == "win32":
        prefix = "json:///"
    else:
        prefix = "json://"
    uri = DataUri(f"{prefix}{path}", None)

    original_data = example_data.generate_example_data()

    proxy = JsonProxy(uri=uri)
    proxy.dump(original_data)
    deserialized_data = proxy.load()
    compare_json.assert_deserialized_data(deserialized_data, original_data)

    serialized_data = json.loads(path.read_text(encoding="utf-8"))
    compare_json.assert_serialized_data(serialized_data["data"], original_data)


def test_nexus_data_persistence(tmp_path):
    path = tmp_path / "data.h5"
    if sys.platform == "win32":
        prefix = "nexus:///"
    else:
        prefix = "nexus://"
    uri = DataUri(f"{prefix}{path}::/result", None)

    original_data = example_data.generate_example_data()
    proxy = NexusProxy(uri=uri)
    proxy.dump(original_data)

    deserialized_data = proxy.load()
    compare_hdf5.assert_deserialized_data(deserialized_data, original_data)

    serialized_data = h5todict(path, "/result", include_attributes=False)
    compare_hdf5.assert_serialized_data(serialized_data, original_data)
