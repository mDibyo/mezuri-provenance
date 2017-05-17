#!/usr/bin/env python3

from lib import PipelineError
from lib.declarations import AbstractComponentProxyFactory


class PipelineSourceStep(object):
    def __init__(self):
        self._is_set = False
        self._context = self.PipelineSourceContext(self)

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def context(self):
        return self._context

    @property
    def output(self):
        return self._context.output

    class PipelineSourceContext(object):
        def __init__(self, step: 'PipelineSourceStep'):
            self._step = step
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
                raise PipelineError('Pipeline Step does not have any outputs.')
            self._step._is_set = True

        def __repr__(self):
            return '{}.context()'.format(repr(self._step))


class PipelineOperationStep(object):
    def __init__(self, **prev_steps):
        self._is_set = False
        self._prev_steps_map = prev_steps
        self._context = self.PipelineOperationContext(self)

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def context(self):
        return self._context

    @property
    def output(self):
        return self._context.output

    class PipelineOperationContext(object):
        def __init__(self, step: 'PipelineOperationStep'):
            self._step = step
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
