from . import graph


@graph
def empty():
    graph = {"id": "empty", "label": "empty", "schema_version": "1.1"}
    return {"graph": graph}, dict()
