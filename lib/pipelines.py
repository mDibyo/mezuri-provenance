#!/usr/bin/env python3

from collections import namedtuple

from lib.declarations import SourceProxyFactory
from utilities import SPEC_IOP_DECLARATION_KEY


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
        self.outputs = None
        self._context = self.PipelineSourceContext(self)

    def context(self):
        return self._context

    class PipelineSourceContext(object):
        def __init__(self, step):
            self._step = step
            self.outputs = PipelineStepOutputs(self._step)

            self._source = None

        def __enter__(self):
            if self._step._is_set:
                raise PipelineError('Pipeline Step already set up.')

            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                return False

            if not len(self.outputs):
                raise PipelineError('Pipeline Step does not have any outputs.')
            self._step.outputs = self.outputs
            self._step._is_set = True

        def __repr__(self):
            return '{}.context()'.format(str(self._step))

        @property
        def source(self):
            if self._source is None:
                raise AttributeError('Pipeline source is not set.')

            return self._source

        @source.setter
        def source(self, new_source: SourceProxyFactory):
            if new_source.data_type != 'SOURCE':
                raise PipelineError('Pipeline Source {} is not valid.'.format(new_source))

            self._source = PipelineSourceStep.PipelineSource(new_source)

    class PipelineSource(object):
        MethodAccess = namedtuple('MethodAccess', ['method_name', 'method_proxy'])

        def __init__(self, source: SourceProxyFactory):
            self.source = source

            self.methods_accessed = []

        def __repr__(self):
            return 'PipelineSource({})'.format(str(self.source))

        def __getattr__(self, method_name):
            method_specs = self.source.specs[SPEC_IOP_DECLARATION_KEY].get(method_name, None)
            if method_specs is None:
                raise AttributeError('Pipeline source does not have output method {}.'.format(method_name))

            method_proxy = self.PipelineSourceMethod(self, method_name, method_specs)
            self.methods_accessed.append(self.MethodAccess(method_name, method_proxy))
            return method_proxy

        class PipelineSourceMethod(object):
            def __init__(self, pipeline_source, method_name, method_specs):
                self.pipeline_source = pipeline_source
                self.method_name = method_name
                self.method_specs = method_specs

                self.query = None

            def __repr__(self):
                return '{}.{}()'.format(str(self.pipeline_source), self.method_name)

            def __call__(self, query):
                self.query = query
                return self.method_specs['output']
