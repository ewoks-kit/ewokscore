import sys

import pytest
from silx.io.dictdump import nxtodict

from ..hashing import UniversalHashable
from ..hashing import uhash
from ..persistence import instantiate_data_proxy
from ..persistence.json import JsonProxy
from ..persistence.nexus import NexusProxy


def test_json_proxy_uri(tmp_path):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = JsonProxy()
    assert proxy.uri is None
    proxy = JsonProxy(uhash_source=hashable)
    assert proxy.uri is None

    if sys.platform == "win32":
        prefix = "json:///"
    else:
        prefix = "json://"

    proxy = JsonProxy(uhash_source=hashable, root_uri=str(tmp_path))
    assert str(proxy.uri) == f"{prefix}{tmp_path/identifier}.json"
    tmpfile = tmp_path / "file"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpfile}.json")
    assert str(proxy.uri) == f"{prefix}{tmpfile/identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpfile}.json?path=/a")
    assert str(proxy.uri) == f"{prefix}{tmpfile/'a'/identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpfile}.json?path=/a/b")
    assert str(proxy.uri) == f"{prefix}{tmpfile/'a'/'b'/identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpfile}.json?path=/a/b/c")
    assert str(proxy.uri) == f"{prefix}{tmpfile/'a'/'b'/'c'/identifier}.json"

    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"{prefix}{tmpfile/'a'/'b'/'c'/identifier}.json"


def test_nexus_proxy_uri(tmp_path):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = NexusProxy()
    assert proxy.uri is None
    proxy = NexusProxy(uhash_source=hashable)
    assert proxy.uri is None

    if sys.platform == "win32":
        prefix = "nexus:///"
    else:
        prefix = "nexus://"

    proxy = NexusProxy(uhash_source=hashable, root_uri=str(tmp_path))
    assert str(proxy.uri) == f"{prefix}{tmp_path/identifier}.nx?path={identifier}"
    tmpfile = tmp_path / "file"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpfile}.nx")
    assert str(proxy.uri) == f"{prefix}{tmpfile}.nx?path={identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpfile}.h5?path=/a")
    assert str(proxy.uri) == f"{prefix}{tmpfile}.h5?path=a/{identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpfile}.nx?path=/a/b")
    assert str(proxy.uri) == f"{prefix}{tmpfile}.nx?path=a/b/{identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpfile}.nx?path=/a/b/c")
    assert str(proxy.uri) == f"{prefix}{tmpfile}.nx?path=a/b/c/{identifier}"

    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"{prefix}{tmpfile}.nx?path=a/b/c/{identifier}"


@pytest.mark.parametrize("scheme", ("json", "nexus"))
@pytest.mark.parametrize("full", (True, False))
def test_proxy_dump(scheme, full, tmp_path):
    if scheme == "nexus":
        extension = ".nx"
    else:
        extension = ".json"

    root_uri = tmp_path
    if full:
        root_uri /= f"dataset{extension}::/scan/task/output_variable_a"

    if sys.platform == "win32":
        root_uri = f"{scheme}:///{root_uri}"
    else:
        root_uri = f"{scheme}://{root_uri}"

    hashable = UniversalHashable(uhash("somedata"))
    proxy = instantiate_data_proxy(
        scheme=scheme, uhash_source=hashable, root_uri=root_uri
    )
    data = [1, 2, 3]
    proxy.dump(data)

    proxy2 = instantiate_data_proxy(
        scheme=scheme, uhash_source=hashable, root_uri=root_uri
    )
    data2 = proxy2.load()
    if scheme == "nexus":
        data2 = data2.tolist()
        adict = nxtodict(str(proxy2.path))
        assert adict["@NX_class"] == "NXroot"
        if full:
            adict = adict["scan"]
            assert adict["@NX_class"] == "NXentry"
            adict = adict["task"]
            assert adict["@NX_class"] == "NXprocess"
            adict = adict["output_variable_a"]
            assert adict["@NX_class"] == "NXcollection"
    assert data == data2
