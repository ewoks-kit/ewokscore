import cProfile
import os
import random
import re
import time
from contextlib import ExitStack
from contextlib import contextmanager
from typing import Any
from typing import Generator
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Type
from typing import Union

from ewoksutils.deprecation_utils import deprecated

from . import events
from . import missing_data
from . import node
from .hashing import UniversalHashable
from .model import BaseInputModel
from .model import BaseOutputModel
from .registration import Registered
from .variable import ReadOnlyVariableContainerNamespace
from .variable import VariableContainer
from .variable import VariableContainerMissingNamespace
from .variable import VariableContainerNamespace


class TaskInputError(ValueError):
    pass


class Task(Registered, UniversalHashable, register=False):
    """Node in a task Graph with named inputs and outputs.

    The universal hash of the task is equal to the universal
    hash of the output. The universal hash of the output is
    equal to the hash of the inputs and the task nonce.

    A task is done when its output exists.

    This is an abstract class. Instantiating a `Task` should be
    done with `ewokscore.inittask.instantiate_task`.
    """

    _INPUT_NAMES: Set[str] = set()
    _OPTIONAL_INPUT_NAMES: Set[str] = set()
    _OUTPUT_NAMES: Set[str] = set()
    _N_REQUIRED_POSITIONAL_INPUTS: int = 0
    _INPUT_MODEL: Optional[Type[BaseInputModel]] = None
    _OUTPUT_MODEL: Optional[Type[BaseOutputModel]] = None

    def __init__(
        self,
        inputs: Optional[Mapping] = None,
        varinfo: Optional[dict] = None,
        node_id: Optional[node.NodeIdType] = None,
        node_attrs: Optional[dict] = None,
        execinfo: Optional[dict] = None,
        profile_directory: Optional[dict] = None,
    ):
        """The named arguments are inputs and Variable configuration"""
        if inputs is None:
            inputs = dict()
        elif not isinstance(inputs, Mapping):
            raise TypeError(inputs, type(inputs))

        # Required outputs for the task to be "done"
        ovars = {varname: self.MISSING_DATA for varname in self._OUTPUT_NAMES}

        # Node/task info
        node_id = node.get_node_id(node_id, node_attrs)
        self.__node_id = node_id
        self.__node_label = node.get_node_label(node_id, node_attrs)
        self.__task_identifier = self._get_task_identifier(inputs)
        task_id = self.class_registry_name()
        task_id = node.get_task_identifier(node_attrs, task_id)
        self.__task_id = task_id
        if node_id and task_id:
            self.__execinfo = execinfo
        else:
            self.__execinfo = None

        # Misc
        self.__exception = None
        self.__succeeded = None
        self._cancelled = False
        self._profile_directory = profile_directory or dict()

        # The output hash will update dynamically if any of the input
        # variables change
        varinfo = node.get_varinfo(node_attrs, varinfo)
        inputs = self._check_inputs(inputs)

        self.__inputs = VariableContainer(value=inputs, varinfo=varinfo)
        self.__inputs_namespace = ReadOnlyVariableContainerNamespace(self.__inputs)
        self.__missing_inputs_namespace = VariableContainerMissingNamespace(
            self.__inputs
        )

        self.__outputs = VariableContainer(
            value=ovars,
            pre_uhash=self.__inputs,
            instance_nonce=self.class_nonce(),
            varinfo=varinfo,
        )
        self.__outputs_namespace = VariableContainerNamespace(self.__outputs)
        self.__missing_outputs_namespace = VariableContainerMissingNamespace(
            self.__outputs
        )

        # The task class has the same hash as its output
        super().__init__(pre_uhash=self.__outputs)

    def _check_inputs(self, inputs: Mapping) -> Mapping:
        """Check inputs without accessing the input values.
        Persisted variables are not loaded.
        """
        input_names = set(inputs.keys())

        # Check required inputs
        missing_required = self.required_input_names() - input_names
        if missing_required:
            self._raise_task_input_error("Missing inputs", str(list(missing_required)))

        # Check required positional inputs
        nrequiredargs = self._N_REQUIRED_POSITIONAL_INPUTS
        for i in range(nrequiredargs):
            if i not in inputs and str(i) not in inputs:
                self._raise_task_input_error(
                    "Missing inputs", f"positional argument #{i}"
                )

        # Init missing optional inputs
        missing_optional = self.optional_input_names() - input_names
        if missing_optional:
            inputs = dict(inputs)
            for varname in missing_optional:
                inputs[varname] = self.MISSING_DATA

        return inputs

    def _validate_inputs(self) -> None:
        """Check inputs with accessing the input values.
        Persisted variables are loaded.

        :raises pydantic.ValidationError:
        """
        if self._INPUT_MODEL is None:
            raise ValueError(
                "Trying to validate inputs while no input model was specified"
            )
        inputs = self.__inputs.get_variable_values()
        model = self._INPUT_MODEL(**inputs)

        for name in self._INPUT_MODEL.model_fields.keys():
            self.__inputs[name].value = getattr(model, name)

    def _validate_outputs(self) -> None:
        """Check outputs with accessing the output values.
        Persisted variables are loaded.

        :raises pydantic.ValidationError:
        """
        if self._OUTPUT_MODEL is None:
            raise ValueError(
                "Trying to validate outputs while no output model was specified"
            )
        outputs = self.__outputs.get_variable_values()
        model = self._OUTPUT_MODEL(**outputs)

        for name in self._OUTPUT_MODEL.model_fields.keys():
            self.__outputs[name].value = getattr(model, name)

    def __init_subclass__(
        subclass,
        input_names: Sequence[str] = tuple(),
        optional_input_names: Sequence[str] = tuple(),
        output_names: Sequence[str] = tuple(),
        n_required_positional_inputs: int = 0,
        input_model: Union[Type[BaseInputModel], None] = None,
        output_model: Union[Type[BaseInputModel], None] = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)

        input_names_set, optional_input_names_set = subclass._generate_inputs_sets(
            input_names,
            optional_input_names,
            n_required_positional_inputs,
            input_model,
        )
        output_names_set = subclass._generate_outputs_set(output_names, output_model)

        reserved = subclass._reserved_variable_names()
        forbidden = input_names_set & reserved
        forbidden |= optional_input_names_set & reserved
        forbidden |= output_names_set & reserved
        if forbidden:
            raise RuntimeError(
                "The following names cannot be used a variable names: "
                + str(list(forbidden))
            )

        # Ensures that each subclass has their own sets:
        subclass._INPUT_NAMES = subclass._INPUT_NAMES | input_names_set
        subclass._OPTIONAL_INPUT_NAMES = (
            subclass._OPTIONAL_INPUT_NAMES | optional_input_names_set
        )
        subclass._OUTPUT_NAMES = subclass._OUTPUT_NAMES | output_names_set
        subclass._N_REQUIRED_POSITIONAL_INPUTS = n_required_positional_inputs
        subclass._INPUT_MODEL = input_model
        subclass._OUTPUT_MODEL = output_model

    @classmethod
    def _generate_inputs_sets(
        subclass,
        input_names: Sequence[str],
        optional_input_names: Sequence[str],
        n_required_positional_inputs: int,
        input_model: Union[Type[BaseInputModel], None],
    ) -> Tuple[Set[str], Set[str]]:
        if input_model is None:
            input_names_set = set(input_names)
            optional_input_names_set = set(optional_input_names)

            has_input_names = bool(
                input_names_set
                or optional_input_names_set
                or n_required_positional_inputs > 0
            )
            if has_input_names and subclass._INPUT_MODEL is not None:
                raise TypeError(
                    f"""Cannot use input_names or optional_input_names since the original task {subclass} uses a input model.
                    Specify inputs via a subclass of the original task input model."""
                )

            return input_names_set, optional_input_names_set

        if not issubclass(input_model, BaseInputModel):
            raise TypeError(
                "input_model should be a subclass of ewokscore.model.BaseInputModel"
            )

        if input_names or optional_input_names or n_required_positional_inputs:
            raise TypeError(
                "input_model cannot be used with input_names, optional_input_names or n_required_positional_inputs. Please use one or the other"
            )

        subclass_has_input_names = bool(
            subclass._INPUT_NAMES
            or subclass._OPTIONAL_INPUT_NAMES
            or subclass._N_REQUIRED_POSITIONAL_INPUTS > 0
        )
        if subclass_has_input_names and subclass._INPUT_MODEL is None:
            raise TypeError(
                f"""Cannot use input_model since the original task {subclass} uses input_names and/or n_required_positional_inputs.
                Specify inputs via a input_names or optional_input_names."""
            )

        if subclass._INPUT_MODEL is not None and not issubclass(
            input_model, subclass._INPUT_MODEL
        ):
            raise TypeError(
                f"Input model {input_model} from task subclass must be a subclass of the original task input model {subclass._INPUT_MODEL}"
            )

        fields = input_model.model_fields
        return (
            set(name for name, field in fields.items() if field.is_required()),
            set(name for name, field in fields.items() if not field.is_required()),
        )

    @classmethod
    def _generate_outputs_set(
        subclass,
        output_names: Sequence[str],
        output_model: Union[Type[BaseOutputModel], None],
    ) -> Set[str]:
        if output_model is None:
            output_names_set = set(output_names)

            has_output_names = bool(output_names_set)
            if has_output_names and subclass._OUTPUT_MODEL is not None:
                raise TypeError(
                    f"""Cannot use output_names since the original task {subclass} uses a output model.
                    Specify outputs via a subclass of the original task output model."""
                )

            return output_names_set

        if not issubclass(output_model, BaseOutputModel):
            raise TypeError(
                "output_model should be a subclass of ewokscore.model.BaseOutputModel"
            )

        if output_names:
            raise TypeError(
                "output_model cannot be used with output_names. Please use one or the other"
            )

        subclass_has_output_names = bool(subclass._OUTPUT_NAMES)
        if subclass_has_output_names and subclass._OUTPUT_MODEL is None:
            raise TypeError(
                f"""Cannot use output_model since the original task {subclass} uses output_names.
                Specify outputs via a output_names."""
            )

        if subclass._OUTPUT_MODEL is not None and not issubclass(
            output_model, subclass._OUTPUT_MODEL
        ):
            raise TypeError(
                f"Output model {output_model} from task subclass must be a subclass of the original task output model {subclass._OUTPUT_MODEL}"
            )

        fields = output_model.model_fields
        return set(fields)

    @staticmethod
    def _reserved_variable_names():
        return VariableContainerNamespace._reserved_variable_names()

    @classmethod
    def instantiate(cls, registry_name: str, **kw):
        r"""Factory method for instantiating a derived class.

        :param str registry_name: for example "tasklib.tasks.MyTask" or "MyTask"
        :param \**kw: `Task` constructor arguments
        :returns Task:
        """
        return cls.get_subclass(registry_name)(**kw)

    @classmethod
    def required_input_names(cls) -> Set[str]:
        if cls._INPUT_MODEL:
            return {
                name
                for name, field in cls._INPUT_MODEL.model_fields.items()
                if field.is_required()
            }
        return cls._INPUT_NAMES

    @classmethod
    def optional_input_names(cls) -> Set[str]:
        if cls._INPUT_MODEL:
            return {
                name
                for name, field in cls._INPUT_MODEL.model_fields.items()
                if not field.is_required()
            }
        return cls._OPTIONAL_INPUT_NAMES

    @classmethod
    def input_names(cls) -> Set[str]:
        if cls._INPUT_MODEL:
            return set(cls._INPUT_MODEL.model_fields)
        return cls._INPUT_NAMES | cls._OPTIONAL_INPUT_NAMES

    @classmethod
    def output_names(cls) -> Set[str]:
        return cls._OUTPUT_NAMES

    @classmethod
    def input_model(cls) -> Optional[Type[BaseInputModel]]:
        return cls._INPUT_MODEL

    @classmethod
    def output_model(cls) -> Optional[Type[BaseOutputModel]]:
        return cls._OUTPUT_MODEL

    @classmethod
    def n_required_positional_inputs(cls) -> int:
        return cls._N_REQUIRED_POSITIONAL_INPUTS

    @classmethod
    def class_nonce_data(cls):
        return super().class_nonce_data() + (
            sorted(cls.input_names()),
            sorted(cls.output_names()),
            cls._N_REQUIRED_POSITIONAL_INPUTS,
        )

    @property
    def input_variables(self) -> VariableContainer:
        if self.__inputs is None:
            raise RuntimeError("references have been removed")
        return self.__inputs

    @property
    def inputs(self) -> ReadOnlyVariableContainerNamespace:
        return self.__inputs_namespace

    @property
    def missing_inputs(self) -> VariableContainerMissingNamespace:
        return self.__missing_inputs_namespace

    def get_input_value(self, key, default: Any = missing_data.MISSING_DATA) -> Any:
        if self.missing_inputs[key]:
            return default
        return self.inputs[key]

    @property
    def input_uhashes(self):
        return self.get_input_uhashes()

    def get_input_uhashes(self):
        return self.__inputs.get_variable_uhashes()

    @property
    @deprecated(
        "the property 'input_values' is deprecated in favor of the function 'get_input_values'"
    )
    def input_values(self):
        """DEPRECATED"""
        return self.get_input_values()

    def get_input_values(self):
        return self.__inputs.get_variable_values()

    @property
    @deprecated(
        "the property 'named_input_values' is deprecated in favor of the function 'get_named_input_values'"
    )
    def named_input_values(self):
        """DEPRECATED"""
        return self.get_named_input_values()

    def get_named_input_values(self):
        return self.__inputs.get_named_variable_values()

    @property
    @deprecated(
        "the property 'positional_input_values' is deprecated in favor of the function 'get_positional_input_values'"
    )
    def positional_input_values(self):
        """DEPRECATED"""
        return self.__inputs.get_positional_input_values()

    def get_positional_input_values(self):
        return self.__inputs.get_positional_variable_values()

    @property
    @deprecated(
        "the property 'npositional_inputs' is deprecated in favor of the property 'n_positional_inputs'"
    )
    def npositional_inputs(self):
        """DEPRECATED"""
        return self.n_positional_inputs

    @property
    def n_positional_inputs(self) -> int:
        return self.__inputs.n_positional_variables

    @property
    def output_variables(self) -> VariableContainer:
        return self.__outputs

    @property
    def missing_outputs(self) -> VariableContainerMissingNamespace:
        return self.__missing_outputs_namespace

    @property
    def outputs(self) -> VariableContainerNamespace:
        return self.__outputs_namespace

    def get_output_value(self, key, default: Any = missing_data.MISSING_DATA) -> Any:
        if self.missing_outputs[key]:
            return default
        return self.outputs[key]

    @property
    @deprecated(
        "the property 'output_uhashes' is deprecated in favor of the function 'get_output_uhashes'"
    )
    def output_uhashes(self):
        """DEPRECATED"""
        return self.get_output_uhashes()

    def get_output_uhashes(self):
        return self.__outputs.get_variable_uhashes()

    @property
    @deprecated(
        "the property 'output_values' is deprecated in favor of the function 'get_output_values'"
    )
    def output_values(self):
        """DEPRECATED"""
        return self.get_output_values()

    def get_output_values(self):
        return self.__outputs.get_variable_values()

    @property
    @deprecated(
        "the property 'output_transfer_data' is deprecated in favor of the function 'get_output_transfer_data'"
    )
    def output_transfer_data(self):
        """DEPRECATED"""
        return self.get_output_transfer_data()

    def get_output_transfer_data(self):
        """The values are either `DataUri` or `Variable`"""
        return self.__outputs.get_variable_transfer_data()

    @property
    def output_metadata(self) -> Union[dict, None]:
        return self.__outputs.metadata

    def _update_output_metadata(self):
        metadata = self.output_metadata
        if metadata is None:
            return
        if self.__node_label:
            metadata.setdefault("title", self.__node_label)

    @property
    def done(self) -> bool:
        """Completed (with or without exception)"""
        return self.failed or self.succeeded

    @property
    def succeeded(self) -> bool:
        """Completed without exception and with output values"""
        if self._OUTPUT_NAMES:
            return self.__outputs.has_value
        else:
            return self.__succeeded

    @property
    def failed(self) -> bool:
        """Completed with exception"""
        return self.__exception is not None

    @property
    def exception(self) -> Optional[Exception]:
        return self.__exception

    def _get_repr_data(self):
        data = super()._get_repr_data()
        if self.__node_label:
            data["label"] = repr(str(self.__node_label))
        else:
            data["label"] = None
        return data

    @property
    def label(self) -> str:
        if self.__node_label:
            return self.__node_label
        else:
            return str(self)

    @property
    def node_id(self) -> node.NodeIdType:
        return self.__node_id

    @property
    def task_identifier(self) -> str:
        return self.__task_identifier

    def _get_task_identifier(self, inputs: Mapping) -> str:
        return self.class_registry_name()

    @property
    def job_id(self) -> Optional[str]:
        if self.__execinfo:
            return self.__execinfo.get("job_id")

    @property
    def workflow_id(self) -> Optional[str]:
        if self.__execinfo:
            return self.__execinfo.get("workflow_id")

    @property
    def _profile_filename(self) -> Optional[str]:
        profile_directory = self._profile_directory
        if not profile_directory:
            return
        job_id = self.job_id
        workflow_id = self.workflow_id
        node_id = self.node_id
        if job_id is None or workflow_id is None or node_id is None:
            return
        if isinstance(node_id, tuple):
            node_id = "_".join(map(str, tuple))
        else:
            node_id = str(node_id)

        job_id = re.sub(r"[^A-Za-z0-9]", "_", job_id)
        workflow_id = re.sub(r"[^A-Za-z0-9]", "_", workflow_id)
        node_id = re.sub(r"[^A-Za-z0-9]", "_", node_id)

        timestamp = int(time.time() * 1000)
        random_chars = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8)
        )
        filename = f"{timestamp}_{random_chars}_{node_id}.prof"

        return os.path.join(profile_directory, workflow_id, job_id, filename)

    def _iter_missing_input_values(self):
        for iname in self._INPUT_NAMES:
            var = self.__inputs.get(iname)
            if var is None or not var.has_value:
                yield iname

    @property
    def is_ready_to_execute(self):
        try:
            next(iter(self._iter_missing_input_values()))
        except StopIteration:
            return True
        return False

    @property
    def cancelled(self) -> bool:
        """Return True if the task has been cancelled by the user"""
        return self._cancelled

    @cancelled.setter
    def cancelled(self, cancelled: bool) -> None:
        self._cancelled = cancelled

    def assert_ready_to_execute(self):
        lst = list(self._iter_missing_input_values())
        if lst:
            self._raise_task_input_error(
                "The following inputs could not be loaded", str(lst)
            )

    def _raise_task_input_error(self, prefix: str, message: str) -> None:
        self._raise_task_error(prefix, message, TaskInputError)

    def _raise_task_error(
        self,
        prefix: str,
        message: str,
        exc_class: Type[Exception],
        cause: Optional[Type[Exception]] = None,
    ) -> None:
        node_id = self.__node_id
        task_identifier = self.task_identifier
        if self.__node_label:
            err_msg = f"{prefix} for ewoks task {self.__node_label!r} (id: {node_id!r}, task: {task_identifier!r}): {message}"
        else:
            err_msg = f"{prefix} for ewoks task (id: {node_id!r}, task: {task_identifier!r}): {message}"
        raise exc_class(err_msg) from cause

    def reset_state(self):
        self._cancelled = False
        self.__exception = None
        self.__succeeded = None
        self.__outputs.reset()

    def execute(
        self,
        force_rerun: Optional[bool] = False,
        raise_on_error: Optional[bool] = True,
        cleanup_references: Optional[bool] = False,
    ):
        with ExitStack() as stack:
            ctx = self._profile_time()
            _ = stack.enter_context(ctx)

            ctx = events.node_context(
                self.__execinfo, node_id=self.__node_id, task_id=self.__task_id
            )
            self.__execinfo = stack.enter_context(ctx)

            self.reset_state()

            ctx = self._send_task_events()
            _ = stack.enter_context(ctx)

            try:
                if force_rerun:
                    # Rerun a task which is already done
                    self.__outputs.force_non_existing()
                if self.done:
                    return
                self.assert_ready_to_execute()

                if self._INPUT_MODEL:
                    self._validate_inputs()

                self.run()

                if self._OUTPUT_MODEL:
                    self._validate_outputs()
                self._update_output_metadata()
                self.__outputs.dump()
                self.__succeeded = True
            except Exception as e:
                self.__exception = e
                if raise_on_error:
                    self._raise_task_error(
                        "Execution failed", str(e), RuntimeError, cause=e
                    )
            finally:
                if cleanup_references:
                    self.cleanup_references()

    @contextmanager
    def _profile_time(self) -> Generator[None, None, None]:
        """Optional time profiling within this context."""
        _profile_filename = self._profile_filename
        if _profile_filename:
            profiler = cProfile.Profile()
            profiler.enable()
        try:
            yield
        finally:
            if _profile_filename:
                profiler.disable()
                os.makedirs(os.path.dirname(_profile_filename), exist_ok=True)
                profiler.dump_stats(_profile_filename)

    @contextmanager
    def _send_task_events(self) -> Generator[None, None, None]:
        """Send an ewoks start event on enter and stop event on exit."""
        self._send_start_event()
        try:
            yield
        finally:
            self._send_send_event()

    def _send_event(self, **kwargs):
        """Send an ewoks event"""
        if self.__execinfo:
            events.send_task_event(execinfo=self.__execinfo, **kwargs)

    def _send_start_event(self):
        input_uris = [
            {"name": name, "value": str(uri) if uri else None}
            for name, uri in self.__inputs.get_variable_uris().items()
        ]
        output_uris = [
            {"name": name, "value": str(uri) if uri else None}
            for name, uri in self.__outputs.get_variable_uris().items()
        ]
        task_uri = self.__outputs.data_uri
        if task_uri:
            task_uri = str(task_uri)
        self._send_event(
            event="start",
            input_uris=input_uris,
            output_uris=output_uris,
            task_uri=task_uri,
        )

    def _send_send_event(self):
        self._send_event(event="end", exception=self.exception)

    def cleanup_references(self):
        """Removes all references to the inputs.
        Side effect: fixes the uhash of the task and outputs
        """
        self.__inputs = None
        self.__inputs_namespace = None
        self.__missing_inputs_namespace = None
        self.__outputs.cleanup_references()
        super().cleanup_references()

    def run(self):
        """To be implemented by the derived classes"""
        raise NotImplementedError

    def cancel(self):
        """
        Function called when a task is cancelled.
        To be implemented by the derived classes
        """
        raise NotImplementedError
