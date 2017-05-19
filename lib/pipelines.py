#!/usr/bin/env python3

from contextlib import contextmanager

from lib import PipelineError
from lib.declarations import PipelineStepContext, AbstractComponentProxyFactory, SourceProxyFactory, OperatorProxyFactory
from utilities import hashes_xor


class PipelineStep(object):
    def __init__(self):
        self._is_set = False

        self._component = None
        self._component_initialized = False
        self._method_calls = []
        self._output = None

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    @property
    def output(self):
        return self._output

    def _validate_and_record_method_call(self, method_call):
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

    @contextmanager
    def context(self):
        if self._is_set:
            raise PipelineError('pipeline step already set up')

        with PipelineStepContext().context(self._validate_and_record_method_call):
            yield self

        if self._output is None:
            raise PipelineError('no component methods have been called for producing output')
        self._is_set = True


class PipelineOperationStep(object):
    def __init__(self, **prev_steps):
        self._is_set = False
        self._prev_steps_map = prev_steps
        self._context = self.PipelineOperationContext(self)

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    @property
    def version_hash(self):
        return hashes_xor(self.operator.version_hash,
                          *map(lambda step: step.version_hash, self._prev_steps_map.values()))

    def context(self):
        return self._context

    @property
    def operator(self) -> OperatorProxyFactory:
        return self._context.operator

    @property
    def output(self):
        return self._context.output

    class PipelineOperationContext(object):
        def __init__(self, step: 'PipelineOperationStep'):
            self._step = step
            self.operator = None
            self.output = None

        def __enter__(self):
            if self._step._is_set:
                raise PipelineError('Pipeline Step already set up.')

            AbstractComponentProxyFactory._in_pipeline_step_context = True
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            AbstractComponentProxyFactory._in_pipeline_step_context = False

            if exc_type is not None:
                return False

            if self.output is None:
                raise PipelineError('Pipeline Operation Step does not have operator')
            if self.output is None:
                raise PipelineError('Pipeline Step does not have any outputs.')
            self._step._is_set = True

        def __repr__(self):
            return '{}.context()'.format(repr(self._step))

        @property
        def prev_steps(self):
            return PipelineOperationStep.PipelineOperationPreviousSteps(self._step)

    class PipelineOperationPreviousSteps(object):
        def __init__(self, proxy: 'PipelineOperationStep'):
            self._proxy = proxy

        def __repr__(self):
            return '{}.prev_steps'.format(repr(self._proxy))

        def __getattr__(self, step_name):
            prev_step = self._proxy._prev_steps_map.get(step_name, None)
            if prev_step is None:
                raise AttributeError('Step with name {} is not a previous step of {}'.format(
                    step_name, str(self._proxy)))

            return prev_step.output


class Pipeline(object):
    def __init__(self, last_step: PipelineSourceStep or PipelineOperationStep):
        self.last_step = last_step

    @property
    def version_hash(self):
        return self.last_step.version_hash
