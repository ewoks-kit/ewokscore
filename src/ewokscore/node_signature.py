import inspect
import logging
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from ewoksutils import import_utils

from ewokscore.model import BaseInputModel
from ewokscore.model import BaseOutputModel
from ewokscore.ppftasks import PPF_DICT_ARGUMENT

from .dynamictask import get_dynamically_task_class
from .missing_data import MISSING_DATA
from .models import EwoksTaskTypeError
from .models import NodeIdType
from .models import NodePort
from .models import NodeSignature
from .task import Task

_logger = logging.getLogger(__name__)


def _get_node_signature(
    task_type: str,
    task_identifier: str,
    default_input_map: Dict[str, Any],
    task_generator: Optional[str],
) -> Tuple[List[NodePort], List[NodePort]]:

    if task_type == "class":
        task_cls = import_utils.import_qualname(task_identifier)
        inputs = list(_node_inputs_from_class(task_cls, default_input_map))
        outputs = list(_node_outputs_from_class(task_cls))
    elif task_type == "generated":
        task_cls = get_dynamically_task_class(task_generator, task_identifier)
        inputs = list(_node_inputs_from_class(task_cls, default_input_map))
        outputs = list(_node_outputs_from_class(task_cls))
    elif task_type == "method":
        task_method = import_utils.import_qualname(task_identifier)
        inputs = list(_node_inputs_from_method(task_method, default_input_map))
        outputs = [
            NodePort(
                name="return_value",
                value=MISSING_DATA,
                required=None,
                description=None,
                examples=None,
            )
        ]
    elif task_type == "ppfmethod":
        task_method = import_utils.import_qualname(task_identifier)
        inputs = list(_node_inputs_from_method(task_method, default_input_map))
        outputs = [
            NodePort(
                name=PPF_DICT_ARGUMENT,
                value=MISSING_DATA,
                required=None,
                description=None,
                examples=None,
            )
        ]
    else:
        raise EwoksTaskTypeError(f"Cannot get inputs from task type {task_type!r}")

    return inputs, outputs


def _node_inputs_from_class(
    task_cls: Type[Task], default_input_map: Dict[str, Any]
) -> Generator[NodePort, None, None]:
    """
    Return all task input parameters based on a task class.
    """
    input_model = task_cls.input_model()
    if input_model:
        yield from _node_ports_from_class_model(input_model, default_input_map)
    else:
        yield from _node_inputs_from_class_methods(task_cls, default_input_map)


def _node_ports_from_class_model(
    model: Union[BaseInputModel, BaseOutputModel],
    default_values: Dict[str, Any],
) -> Generator[NodePort, None, None]:
    """
    Return all task input or output parameters based on a model.
    """
    for name, field in model.model_fields.items():
        required = field.is_required()

        if name in default_values:
            # Default value overwrites model default (if any)
            value = default_values[name]
        else:
            try:
                default = field.get_default()
            except Exception:
                # Field has no default value
                value = MISSING_DATA
            else:
                # Field has a default value
                value = default

        yield NodePort(
            name=name,
            required=required,
            value=value,
            description=field.description,
            examples=field.examples,
        )


def _node_inputs_from_class_methods(
    task_cls: Type[Task], default_input_map: Dict[str, Any]
) -> Generator[NodePort, None, None]:
    """
    Return all task input parameters based on a task class.
    """
    input_names = [(name, True) for name in sorted(task_cls.required_input_names())]
    input_names += [(name, False) for name in sorted(task_cls.optional_input_names())]

    for name, required in input_names:
        value = default_input_map.get(name, MISSING_DATA)
        yield NodePort(
            name=name,
            required=required,
            value=value,
            description=None,
            examples=None,
        )


def _node_inputs_from_method(
    task_method: Callable, default_input_map: Dict[str, Any]
) -> Generator[NodePort, None, None]:
    """
    Return all task input parameters based on a task method.
    """
    sig = inspect.signature(task_method)
    for name, param in sig.parameters.items():
        if param.kind in (param.kind.VAR_POSITIONAL, param.kind.VAR_KEYWORD):
            continue

        required = param.default is inspect.Parameter.empty
        if name in default_input_map:
            # Default input overwrites parameter default (if any)
            value = default_input_map[name]
        elif required:
            # Parameter has no default value
            value = MISSING_DATA
        else:
            # Parameter has a default value
            value = param.default

        yield NodePort(
            name=name,
            required=required,
            value=value,
            description=None,
            examples=None,
        )


def _node_outputs_from_class(task_cls: Type[Task]) -> Generator[NodePort, None, None]:
    """
    Return all task output parameters based on a task class.
    """
    output_model = task_cls.output_model()
    if output_model:
        yield from _node_ports_from_class_model(output_model, dict())
    else:
        yield from _node_outputs_from_class_methods(task_cls)


def _node_outputs_from_class_methods(task_cls) -> Generator[NodePort, None, None]:
    for name in sorted(task_cls.output_names()):
        yield NodePort(
            name=name,
            value=MISSING_DATA,
            required=None,
            description=None,
            examples=None,
        )


def _node_inputs_from_defaults(
    default_input_map: Dict[str, Any],
) -> Generator[NodePort, None, None]:
    for name, value in default_input_map.items():
        yield NodePort(
            name=name,
            required=True,
            value=value,
            description=None,
            examples=None,
        )


def node_signature(node_id: NodeIdType, node_attrs: Dict[str, Any]) -> NodeSignature:
    """
    Return the input and output parameters of a node.
    """
    task_type = node_attrs["task_type"]
    task_identifier = node_attrs["task_identifier"]
    default_inputs = node_attrs.get("default_inputs", [])
    default_input_map = {item["name"]: item.get("value") for item in default_inputs}

    try:
        inputs, outputs = _get_node_signature(
            task_type,
            task_identifier,
            default_input_map,
            task_generator=node_attrs.get("task_generator"),
        )
        import_error = None
    except Exception as e:
        if isinstance(e, ImportError):
            _logger.warning(f"Cannot import {task_identifier!r}: {e}")
        elif isinstance(e, EwoksTaskTypeError):
            _logger.warning(
                f"Task type {task_type!r} is not supported ({task_identifier!r}). Only using default values from the workflow."
            )
        else:
            _logger.warning(e, exc_info=True)
        inputs = list(_node_inputs_from_defaults(default_input_map))
        outputs = []
        import_error = e

    return NodeSignature(
        id=node_id,
        label=node_attrs.get("label", None),
        task_identifier=task_identifier,
        import_error=import_error,
        inputs=inputs,
        outputs=outputs,
    )
