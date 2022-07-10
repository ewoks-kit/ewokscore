import pytest


@pytest.fixture
def varinfo(tmpdir):
    yield {"root_uri": str(tmpdir)}
