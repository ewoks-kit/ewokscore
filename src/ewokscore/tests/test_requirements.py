from ewokscore.requirements import extract_requirements
from ewokscore.tests.examples.graphs import get_graph


def test_extract_requirements():
    workflow, _ = get_graph("demo")

    assert extract_requirements(workflow) == ["ewokscore"]
