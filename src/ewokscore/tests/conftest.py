import pytest
from jupyter_client.kernelspec import KernelSpecManager
from ipykernel.kernelspec import install as install_kernel

from packaging.version import parse as parse_version
from ewokscore.graph.schema import SchemaMetadata, get_versions


@pytest.fixture
def varinfo(tmpdir):
    yield {"root_uri": str(tmpdir)}


@pytest.fixture(scope="session")
def testkernel():
    m = KernelSpecManager()
    kernel_name = "pytest_kernel"
    install_kernel(kernel_name=kernel_name, user=True)
    yield kernel_name
    m.remove_kernel_spec(kernel_name)


@pytest.fixture
def use_test_schema_versions(monkeypatch):
    from ewokscore.graph import schema

    def no_update(graph):
        pass

    def backward_update(graph):
        graph.graph["schema_version"] = "0.1"

    def update_from_v0_2_to_1_0(graph):
        graph.graph["schema_version"] = "1.0"

    def get_test_versions():
        return {
            parse_version("0.1"): SchemaMetadata(("0.1.0-rc", None), no_update),
            parse_version("0.2"): SchemaMetadata(
                ("0.1.0-rc", None), update_from_v0_2_to_1_0
            ),
            parse_version("0.3"): SchemaMetadata(("0.1.0-rc", None), backward_update),
            **get_versions(),
        }

    monkeypatch.setattr(schema, "get_versions", get_test_versions)
