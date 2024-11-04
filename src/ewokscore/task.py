import os
import re
import time
import random
import warnings
import cProfile
from typing import Any, Optional, Union, Mapping, Generator
from contextlib import ExitStack
from contextlib import contextmanager

from .hashing import UniversalHashable
from .registration import Registered
from .variable import VariableContainer
from .variable import VariableContainerNamespace
from .variable import ReadOnlyVariableContainerNamespace
from .variable import VariableContainerMissingNamespace
from . import node
from . import missing_data
from . import events


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

    _INPUT_NAMES = set()
    _OPTIONAL_INPUT_NAMES = set()
    _OUTPUT_NAMES = set()
    _N_REQUIRED_POSITIONAL_INPUTS = 0

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

        # Check required inputs
        missing_required = set(self._INPUT_NAMES) - set(inputs.keys())
        if missing_required:
            raise TaskInputError(f"Missing inputs for {type(self)}: {missing_required}")

        # Check required positional inputs
        nrequiredargs = self._N_REQUIRED_POSITIONAL_INPUTS
        for i in range(nrequiredargs):
            if i not in inputs and str(i) not in inputs:
                raise TaskInputError(
                    f"Missing inputs for {type(self)}: positional argument #{i}"
                )

        # Init missing optional inputs
        missing_optional = set(self._OPTIONAL_INPUT_NAMES) - set(inputs.keys())
        for varname in missing_optional:
            inputs[varname] = self.MISSING_DATA

        # Required outputs for the task to be "done"
        ovars = {varname: self.MISSING_DATA for varname in self._OUTPUT_NAMES}

        # Node/task info
        node_id = node.get_node_id(node_id, node_attrs)
        self.__node_id = node_id
        self.__node_label = node.get_node_label(node_id, node_attrs)
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
        self.__inputs = VariableContainer(value=inputs, varinfo=varinfo)
        self.__outputs = VariableContainer(
            value=ovars,
            pre_uhash=self.__inputs,
            instance_nonce=self.class_nonce(),
            varinfo=varinfo,
        )

        self.__inputs_namespace = ReadOnlyVariableContainerNamespace(self.__inputs)
        self.__outputs_namespace = VariableContainerNamespace(self.__outputs)

        self.__missing_inputs_namespace = VariableContainerMissingNamespace(
            self.__inputs
        )
        self.__missing_outputs_namespace = VariableContainerMissingNamespace(
            self.__outputs
        )

        # The task class has the same hash as its output
        super().__init__(pre_uhash=self.__outputs)

    def __init_subclass__(
        subclass,
        input_names=tuple(),
        optional_input_names=tuple(),
        output_names=tuple(),
        n_required_positional_inputs=0,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        input_names = set(input_names)
        optional_input_names = set(optional_input_names)
        output_names = set(output_names)

        reserved = subclass._reserved_variable_names()
        forbidden = input_names & reserved
        forbidden |= optional_input_names & reserved
        forbidden |= output_names & reserved
        if forbidden:
            raise RuntimeError(
                "The following names cannot be used a variable names: "
                + str(list(forbidden))
            )

        # Ensures that each subclass has their own sets:
        subclass._INPUT_NAMES = subclass._INPUT_NAMES | set(input_names)
        subclass._OPTIONAL_INPUT_NAMES = subclass._OPTIONAL_INPUT_NAMES | set(
            optional_input_names
        )
        subclass._OUTPUT_NAMES = subclass._OUTPUT_NAMES | set(output_names)
        subclass._N_REQUIRED_POSITIONAL_INPUTS = n_required_positional_inputs

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
    def required_input_names(cls):
        return cls._INPUT_NAMES

    @classmethod
    def optional_input_names(cls):
        return cls._OPTIONAL_INPUT_NAMES

    @classmethod
    def input_names(cls):
        return cls._INPUT_NAMES | cls._OPTIONAL_INPUT_NAMES

    @classmethod
    def output_names(cls):
        return cls._OUTPUT_NAMES

    @classmethod
    def class_nonce_data(cls):
        return super().class_nonce_data() + (
            sorted(cls.input_names()),
            sorted(cls.output_names()),
            cls._N_REQUIRED_POSITIONAL_INPUTS,
        )

    @property
    def input_variables(self):
        if self.__inputs is None:
            raise RuntimeError("references have been removed")
        return self.__inputs

    @property
    def inputs(self):
        return self.__inputs_namespace

    @property
    def missing_inputs(self):
        return self.__missing_inputs_namespace

    def get_input_value(self, key, default: Any = missing_data.MISSING_DATA):
        if self.missing_inputs[key]:
            return default
        return self.inputs[key]

    @property
    def input_uhashes(self):
        return self.get_input_uhashes()

    def get_input_uhashes(self):
        return self.__inputs.get_variable_uhashes()

    @property
    def input_values(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'input_values' is deprecated in favor of the function 'get_input_values'",
            DeprecationWarning,
        )
        return self.get_input_values()

    def get_input_values(self):
        return self.__inputs.get_variable_values()

    @property
    def named_input_values(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'named_input_values' is deprecated in favor of the function 'get_named_input_values'",
            DeprecationWarning,
        )
        return self.get_named_input_values()

    def get_named_input_values(self):
        return self.__inputs.get_named_variable_values()

    @property
    def positional_input_values(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'positional_input_values' is deprecated in favor of the function 'get_positional_input_values'",
            DeprecationWarning,
        )
        return self.__inputs.get_positional_input_values()

    def get_positional_input_values(self):
        return self.__inputs.get_positional_variable_values()

    @property
    def npositional_inputs(self):
        return self.__inputs.n_positional_variables

    @property
    def output_variables(self):
        return self.__outputs

    @property
    def missing_outputs(self):
        return self.__missing_outputs_namespace

    @property
    def outputs(self):
        return self.__outputs_namespace

    def get_output_value(self, key, default: Any = missing_data.MISSING_DATA):
        if self.missing_outputs[key]:
            return default
        return self.outputs[key]

    @property
    def output_uhashes(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'output_uhashes' is deprecated in favor of the function 'get_output_uhashes'",
            DeprecationWarning,
        )
        return self.get_output_uhashes()

    def get_output_uhashes(self):
        return self.__outputs.get_variable_uhashes()

    @property
    def output_values(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'output_values' is deprecated in favor of the function 'get_output_values'",
            DeprecationWarning,
        )
        return self.get_output_values()

    def get_output_values(self):
        return self.__outputs.get_variable_values()

    @property
    def output_transfer_data(self):
        """DEPRECATED"""
        warnings.warn(
            "the property 'output_transfer_data' is deprecated in favor of the function 'get_output_transfer_data'",
            DeprecationWarning,
        )
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
    def done(self):
        """Completed (with or without exception)"""
        return self.failed or self.succeeded

    @property
    def succeeded(self):
        """Completed without exception and with output values"""
        if self._OUTPUT_NAMES:
            return self.__outputs.has_value
        else:
            return self.__succeeded

    @property
    def failed(self):
        """Completed with exception"""
        return self.__exception is not None

    @property
    def exception(self):
        return self.__exception

    def _get_repr_data(self):
        data = super()._get_repr_data()
        if self.__node_label:
            data["label"] = repr(str(self.__node_label))
        else:
            data["label"] = None

    @property
    def label(self):
        if self.__node_label:
            return self.__node_label
        else:
            return str(self)

    @property
    def node_id(self) -> node.NodeIdType:
        return self.__node_id

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
            raise TaskInputError(
                "The following inputs could not be loaded: " + str(lst)
            )

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

                self.run()

                self._update_output_metadata()
                self.__outputs.dump()
                self.__succeeded = True
            except Exception as e:
                self.__exception = e
                if raise_on_error:
                    raise RuntimeError(f"Task '{self.label}' failed") from e
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
