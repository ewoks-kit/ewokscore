import pytest
from jupyter_client.kernelspec import KernelSpecManager
from ipykernel.kernelspec import install as install_kernel


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
