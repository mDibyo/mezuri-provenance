#!/usr/bin/env python3

from collections import namedtuple

from utilities import SingletonClass

MethodCall = namedtuple('MethodCall', ['class_', 'method', 'inputs', 'output_specs'])


class PipelineStepContext(SingletonClass):
    _in_context = False  # This is not thread-safe.
    _callback = None

    @property
    def in_context(self):
        return self._in_context

    def context(self, callback=None):
        self._callback = callback
        return self

    def __enter__(self):
        self._in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False
        self._callback = None

    def add_method_call_in_context(self, method_call: MethodCall):
        if self._in_context and self._callback is not None:
            self._callback(method_call)
