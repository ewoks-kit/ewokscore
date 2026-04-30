import json
import sys

from ...persistence.json import JsonProxy
from ...persistence.proxy import DataUri
from . import example_data


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
    python_data = proxy.load()
    example_data.assert_python_data(python_data, original_data)

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    example_data.assert_raw_data(raw_data, original_data)
