import logging

import pytest

from ..graph import load_graph
from ..graph.schema import LATEST_VERSION
from ..graph.schema import get_versions

LATEST_VERSION = str(LATEST_VERSION)


def test_update_method_with_exception():
    with pytest.raises(
        ValueError,
        match='Graph schema version "0.0" requires another library version: python3 -m pip install "ewokscore>=0.0,<0.0.1"',
    ):
        load_graph({"graph": {"id": "test", "schema_version": "0.0"}})


def test_graph_version(caplog):
    # Update of the default version
    with caplog.at_level(logging.WARNING):
        assert_load({"graph": {"id": "test"}})

    # Update of the latest version
    assert_load({"graph": {"id": "test", "schema_version": LATEST_VERSION}})


def test_correct_update_method(use_test_schema_versions):
    assert_load({"graph": {"id": "test", "schema_version": "0.2"}})


def test_error_on_improper_update_methods(use_test_schema_versions):
    # Update method which does not change the version
    with pytest.raises(
        RuntimeError,
        match="graph conversion did not update the schema version",
    ):
        load_graph({"graph": {"id": "test", "schema_version": "0.1"}})

    # Update method which downgrades the version
    with pytest.raises(
        RuntimeError,
        match="graph conversion did not increment the schema version",
    ):
        load_graph({"graph": {"id": "test", "schema_version": "0.3"}})


def test_non_existing_version():
    with pytest.raises(
        ValueError,
        match='Graph schema version "99999.0" is either invalid or requires a newer library version: python3 -m pip install --upgrade ewokscore',
    ):
        load_graph({"graph": {"id": "test", "schema_version": "99999.0"}})


def assert_load(adict: dict):
    assert load_graph(adict).graph.graph["schema_version"] == LATEST_VERSION


def assert_latest_version_exists():
    assert LATEST_VERSION in get_versions()
