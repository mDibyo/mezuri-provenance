#!/usr/bin/env python3

from contextlib import contextmanager

from lib import PipelineError
from ._pipelinecontext import MethodCall, StepOutputAccess, PipelineStepContext
from utilities import hashes_xor


class PipelineStep(object):
    def __init__(self):
        self._is_set = False
        self._reset()

    def _reset(self):
        self._is_set = False

        self._component = None
        self._component_initialized = False
        self._method_calls = []
        self._output = None
        self._prev_steps = set()

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    @property
    def output(self):
        PipelineStepContext().add_step_output_access_in_context(StepOutputAccess(self))
        return self._output

    def _validate_and_record_method_call(self, method_call: MethodCall):
        component_class = method_call.class_
        if self._component is not None:
            if component_class != self._component:
                raise PipelineError('component {} used when component {} is already being used '
                                    'in step'.format(component_class, self._component))
        else:
            self._component = component_class

        if method_call.method == '__init__':
            if self._component_initialized:
                raise PipelineError('component being reinitialized in step')
            self._component_initialized = True
        else:
            if self._output is not None:
                raise PipelineError('a component method has already been called')
            self._output = method_call.output_specs

        self._method_calls.append(method_call)

    def _record_step_output_access(self, step_output_access: StepOutputAccess):
        self._prev_steps.add(step_output_access.step)

    @contextmanager
    def context(self):
        if self._is_set:
            raise PipelineError('pipeline step already set up')

        try:
            with PipelineStepContext().context(self._validate_and_record_method_call,
                                               self._record_step_output_access):
                yield self
        except:
            self._reset()
            raise

        if self._output is None:
            raise PipelineError('no component methods have been called for producing output')
        self._is_set = True


class Pipeline(object):
    def __init__(self, last_step: PipelineStep):
        self.last_step = last_step

    @property
    def version_hash(self):
        return self.last_step.version_hash
