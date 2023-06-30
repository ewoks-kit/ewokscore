import json
import logging
from typing import Optional

try:
    from papermill import execute_notebook
except ImportError:
    execute_notebook = None

from .task import Task

NOTEBOOK_ARGUMENT = "_notebook"
RESULT_TAG = "results"

logger = logging.getLogger(__name__)


class NotebookExecutorTask(
    Task,
    input_names=[NOTEBOOK_ARGUMENT],
    optional_input_names=["_output_notebook", "_kernel_name", "_execution_timeout"],
    output_names=["output_notebook", "results"],
):
    NOTEBOOK_ARGUMENT = NOTEBOOK_ARGUMENT

    def run(self):
        if execute_notebook is None:
            raise ImportError("requires papermill")
        parameters = self.get_input_values()
        reserved = self.input_names()
        parameters = {k: v for k, v in parameters.items() if k not in reserved}
        kernel_name = self.get_input_value("_kernel_name", None)
        output_notebook = self.get_input_value("_output_notebook", None)
        execution_timeout = self.get_input_value("_execution_timeout", None)
        self.outputs.results = _execute_notebook(
            self.inputs._notebook,
            parameters,
            output_notebook=output_notebook,
            kernel_name=kernel_name,
            execution_timeout=execution_timeout,
        )
        self.outputs.output_notebook = output_notebook


def _execute_notebook(
    input_notebook: str,
    parameters: dict,
    output_notebook: Optional[str] = None,
    kernel_name: Optional[str] = None,
    execution_timeout: Optional[float] = None,
) -> dict:
    level = logger.getEffectiveLevel()
    progress_bar = level and level <= logging.INFO
    nb = execute_notebook(
        input_notebook,
        output_notebook,
        parameters=parameters,
        kernel_name=kernel_name,
        progress_bar=progress_bar,
        execution_timeout=execution_timeout,
    )
    return _extract_results(nb)


def _extract_results(nb) -> dict:
    results = dict()
    for cell in nb.cells:
        metadata = cell["metadata"]
        if "tags" not in metadata or RESULT_TAG not in metadata["tags"]:
            continue
        for output in cell["outputs"]:
            if output["output_type"] != "execute_result":
                continue
            adict = _decode_data(cell, output["data"])
            results.update(adict)
    return results


def _decode_data(cell, data: dict) -> dict:
    jsondata = data.get("application/json")
    if jsondata:
        return jsondata

    txtdata = data.get("text/plain")
    if not txtdata:
        return dict()
    try:
        # Try JSON decoding (e.g. for numbers)
        results = json.loads(txtdata)
    except Exception:
        results = txtdata

    if isinstance(results, dict):
        return results
    key = cell["source"].splitlines()[-1]
    return {key: results}
