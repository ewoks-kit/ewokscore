import pytest

from .. import workflow_discovery
from .conftest import expected_workflows


@pytest.mark.parametrize("workflow_extension", ["json", "yaml", None])
def test_discover_workflows_from_one_module(workflow_extension):
    expected = expected_workflows(
        "ewokscore.tests.examples.loadtest", workflow_extension
    )

    workflows = workflow_discovery.discover_workflows_from_modules(
        "ewokscore.tests.examples.loadtest.*", workflow_extension=workflow_extension
    )
    assert set(workflows) == set(expected)


@pytest.mark.parametrize("workflow_extension", ["json", "yaml", None])
def test_discover_workflows_from_module_pattern(workflow_extension):
    expected = expected_workflows(
        "ewokscore.tests.examples.loadtest", workflow_extension
    )

    workflows = workflow_discovery.discover_workflows_from_modules(
        "ewokscore.tests.ex*.loadtest.*", workflow_extension=workflow_extension
    )
    assert set(workflows) == set(expected)


@pytest.mark.parametrize("workflow_extension", ["json", "yaml", None])
def test_all_workflows_discovery(monkeypatch, workflow_extension):
    expected = expected_workflows(
        "ewokscore.tests.examples.loadtest", workflow_extension
    )

    monkeypatch.setattr(workflow_discovery, "entry_points", _mock_entry_points)

    workflows = workflow_discovery.discover_all_workflows(
        workflow_extension=workflow_extension
    )

    assert set(workflows) == set(expected)


class _MockEntryPoint:
    def __init__(self, name):
        self.name = name


def _mock_entry_points(group):
    assert group == "ewoks.workflows"
    return [
        _MockEntryPoint("ewokscore.tests.examples.loadtest.*"),
        _MockEntryPoint("ewokscore.tests.examples.loadtest.*"),
    ]
