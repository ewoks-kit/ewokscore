import pytest
from ewokscore.hashing import UniversalHashable, uhash
from ewokscore.persistence.json import JsonProxy
from ewokscore.persistence.nexus import NexusProxy


def test_json_proxy_uri(tmpdir):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = JsonProxy(None)
    assert proxy.uri is None
    proxy = JsonProxy(hashable)
    assert proxy.uri is None
    proxy = JsonProxy(hashable, root_uri=str(tmpdir))
    assert str(proxy.uri) == f"json://{tmpdir}/{identifier}.json"
    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"json://{tmpdir}/{identifier}.json"


def test_nexus_proxy_uri(tmpdir):
    hashable = UniversalHashable(uhash("somedata"))
    identifier = str(hashable.uhash)
    proxy = NexusProxy(None)
    assert proxy.uri is None
    proxy = NexusProxy(hashable)
    assert proxy.uri is None
    proxy = NexusProxy(hashable, root_uri=f"{tmpdir}")
    assert (
        str(proxy.uri)
        == f"nexus://{tmpdir}/{identifier}.nx?path=ewoks_results/{identifier}"
    )
    proxy = NexusProxy(hashable, root_uri=f"{tmpdir}/file.nx")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=ewoks_results/{identifier}"
    proxy = NexusProxy(hashable, root_uri=f"{tmpdir}/file.nx?path=/a")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=a/{identifier}"
    proxy = NexusProxy(hashable, root_uri=f"{tmpdir}/file.nx?path=/a/b")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=a/b_{identifier}"
    proxy = NexusProxy(hashable, root_uri=f"{tmpdir}/file.nx?path=/a/b/c")
    assert str(proxy.uri) == f"nexus://{tmpdir}/file.nx?path=a/b/c_{identifier}"
    proxy2 = JsonProxy(proxy.uri)
    assert proxy.uri == proxy2.uri
    assert str(proxy2.uri) == f"nexus://{tmpdir}/file.nx?path=a/b/c_{identifier}"


@pytest.mark.parametrize("full", [True, False])
def test_json_nexus_dump(full, tmpdir):
    if full:
        root_uri = str(tmpdir / "dataset.nx") + "::/scan"
    else:
        root_uri = str(tmpdir)
    hashable = UniversalHashable(uhash("somedata"))
    proxy = NexusProxy(hashable, root_uri=root_uri)
    proxy.dump({"myvalue": 999})

    dproxy = NexusProxy(hashable, root_uri=f"{root_uri}?name=data")
    expected = [1, 2, 3]
    dproxy.dump(expected)
    data = dproxy.load()
    assert len(tmpdir.listdir()) == 1
    assert data.tolist() == expected

    adict = proxy.load()
    adict["data"] = adict["data"].tolist()
    adict["myvalue"] = adict["myvalue"].item()
    adict["uhash"] = adict["uhash"].item()
    assert adict == {
        "@NX_class": "NXprocess",
        "data": [1, 2, 3],
        "uhash": str(hashable.uhash),
        "myvalue": 999,
    }
