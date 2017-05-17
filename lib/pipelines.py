#!/usr/bin/env python3

from lib.declarations import AbstractComponentProxyFactory


class PipelineError(BaseException):
    pass


class PipelineStepOutputs(object):
    def __init__(self, step):
        self._step = step
        self._outputs = {}

    def __repr__(self):
        return str(self._outputs)

    def __len__(self):
        return len(self._outputs)

    def __setattr__(self, key: str, value):
        if key not in ['_outputs', '_step']:
            self._outputs[key] = value

        super().__setattr__(key, value)


class PipelineSourceStep(object):
    def __init__(self):
        self._is_set = False
        self._context = self.PipelineSourceContext(self)

    def context(self):
        return self._context

    @property
    def output(self):
        return self._context.output

    class PipelineSourceContext(object):
        def __init__(self, step):
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
