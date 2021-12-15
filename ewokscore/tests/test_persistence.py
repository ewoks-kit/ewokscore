import pytest
from silx.io.dictdump import nxtodict
from ewokscore.hashing import UniversalHashable, uhash
from ewokscore.persistence.json import JsonProxy
from ewokscore.persistence.nexus import NexusProxy
from ewokscore.persistence import instantiate_data_proxy


def test_json_proxy_uri(tmpdir):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = JsonProxy()
    assert proxy.uri is None
    proxy = JsonProxy(uhash_source=hashable)
    assert proxy.uri is None

    proxy = JsonProxy(uhash_source=hashable, root_uri=str(tmpdir))
    assert str(proxy.uri) == f"json://{tmpdir}/{identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.json")
    assert str(proxy.uri) == f"json://{tmpdir}/file/{identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.json?path=/a")
    assert str(proxy.uri) == f"json://{tmpdir}/file/a/{identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.json?path=/a/b")
    assert str(proxy.uri) == f"json://{tmpdir}/file/a/b/{identifier}.json"
    proxy = JsonProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.json?path=/a/b/c")
    assert str(proxy.uri) == f"json://{tmpdir}/file/a/b/c/{identifier}.json"

    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"json://{tmpdir}/file/a/b/c/{identifier}.json"


def test_nexus_proxy_uri(tmpdir):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = NexusProxy()
    assert proxy.uri is None
    proxy = NexusProxy(uhash_source=hashable)
    assert proxy.uri is None

    proxy = NexusProxy(uhash_source=hashable, root_uri=str(tmpdir))
    assert str(proxy.uri) == f"nexus://{tmpdir}/{identifier}.nx?path={identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.nx")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path={identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.h5?path=/a")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.h5?path=a/{identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.nx?path=/a/b")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=a/b/{identifier}"
    proxy = NexusProxy(uhash_source=hashable, root_uri=f"{tmpdir}/file.nx?path=/a/b/c")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=a/b/c/{identifier}"

    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"nexus://{tmpdir}/file.nx?path=a/b/c/{identifier}"


@pytest.mark.parametrize("scheme", ("json", "nexus"))
@pytest.mark.parametrize("full", (True, False))
def test_proxy_dump(scheme, full, tmpdir):
    if scheme == "nexus":
        extension = ".nx"
    else:
        extension = ".json"

    root_uri = tmpdir
    if full:
        root_uri /= f"dataset{extension}::/scan/task/output_variable_a"
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
