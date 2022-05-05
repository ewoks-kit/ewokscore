import pytest
import logging
from ewokscore.graph import load_graph
from ewokscore.graph.update import LATEST_VERSION

LATEST_VERSION = str(LATEST_VERSION)


def test_graph_version(caplog):
    # Update of the default version
    with caplog.at_level(logging.WARNING):
        assert_load({})

    # Update of the latest version
    assert_load({"graph": {"version": LATEST_VERSION}})

    # Update method which raises an exception
    with pytest.raises(
        ValueError,
        match='Graph version "0.0" requires another library version: python -m pip install "ewokscore>=0.0,<0.0.1"',
    ):
        load_graph({"graph": {"version": "0.0"}})

    # Update method which does not update the version
    with pytest.raises(
        AssertionError,
        match="graph conversion did not update the version",
    ):
        load_graph({"graph": {"version": "0.1"}})

    # Correct update method
    assert_load({"graph": {"version": "0.2"}})

    # Version does not exist
    with pytest.raises(
        ValueError,
        match='Graph version "99999.0" is either invalid or requires a newer library version: python -m pip install --upgrade ewokscore',
    ):
        load_graph({"graph": {"version": "99999.0"}})


def assert_load(adict: dict):
    load_graph(adict).graph.graph["version"] == LATEST_VERSION
