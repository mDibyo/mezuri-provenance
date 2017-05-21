#!/usr/bin/env python3

from collections import namedtuple

from common import SingletonClass, get_hashable_dict


class MethodCall(namedtuple('MethodCall', ['class_', 'method', 'inputs', 'output_specs'])):
    def __hash__(self):
        return hash((self.class_, self.method, get_hashable_dict(self.inputs),
                     get_hashable_dict(self.output_specs)))


StepOutputAccess = namedtuple('StepOutputAccess', ['step'])


class PipelineStepContext(SingletonClass):
    _in_ctx = False  # This is not thread-safe.
    _mc_callback = None
    _soa_callback = None

    @property
    def in_context(self):
        return self._in_ctx

    def context(self, method_call_callback=None, step_output_access_callback=None):
        self._mc_callback = method_call_callback
        self._soa_callback = step_output_access_callback
        return self

    def __enter__(self):
        self._in_ctx = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_ctx = False
        self._mc_callback = None

    def add_method_call_in_context(self, method_call: MethodCall):
        if self._in_ctx and self._mc_callback is not None:
            self._mc_callback(method_call)

    def add_step_output_access_in_context(self, step_output_access: StepOutputAccess):
        if self._in_ctx and self._soa_callback is not None:
            self._soa_callback(step_output_access)
