#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict, Callable, Tuple

from . import PipelineError
from ._pipelinecontext import MethodCall, PipelineStepContext
from common import ComponentInfo, SPEC_DEFINITION_KEY, SPEC_IOP_DECLARATION_KEY
from common.registry import RegistryClient
import lib.types as mezuri_types

PARAM_METHOD_DECLARATION_ATTR = '__mezuri_param_method__'
IO_METHOD_DECLARATION_ATTR = '__mezuri_io_method__'


class AbstractComponentProxyFactory(mezuri_types.AbstractMezuriSerializable):
    data_type = 'ABSTRACT_COMPONENT'

    @classmethod
    @property
    @abstractmethod
    def component_type(cls):
        return NotImplemented

    def __init__(self, registry_url: str, name: str, version: str):
        self.registry_url = registry_url
        self.name = name
        self.version_str = version

        self._specs = None
        self._version_hash = None

    def __repr__(self):
        if self._specs is None:
            return '{}({}, {}, {})'.format(self.__class__.__name__, self.registry_url,
                                           self.name, self.version_str)

        return 'Proxy({})'.format(self._specs[SPEC_DEFINITION_KEY]['class'])

    @property
    def info(self) -> ComponentInfo:
        return ComponentInfo(self.component_type, self.registry_url, self.name, self.version_str)

    def __eq__(self, other):
        return self.info == other.info

    def __hash__(self):
        return hash(self.info)

    def serialize(self):
        return mezuri_types.Serialized(self.data_type, (self.registry_url, self.name, self.version_str))

    @classmethod
    def deserialize(cls, contents):
        registry_url, name, version_str = contents
        return cls(registry_url, name, version_str)

    @property
    def dependencies(self):
        return {self}

    def _fetch_spec_and_version_hash(self):
        registry = RegistryClient(self.registry_url, self.component_type, self.name)
        component_version = registry.get_component_version(self.version_str)
        self._specs, self._version_hash = component_version['specs'], component_version['hash']

    @property
    def specs(self) -> Dict:
        if self._specs is None:
            self._fetch_spec_and_version_hash()
        return self._specs

    @property
    def version_hash(self):
        if self._version_hash is None:
            self._fetch_spec_and_version_hash()
        return self._version_hash

    @abstractmethod
    def __call__(self, **kwargs):
        if not PipelineStepContext().in_context:
            raise PipelineError('{}() can only be called in a pipeline step context'.format(str(self)))

        PipelineStepContext().add_method_call_in_context(MethodCall(
            self, '__init__', kwargs, {}))

        return self

    class ComponentMethodProxy(object):
        def __init__(self, proxy: 'AbstractComponentProxyFactory', method_name: str, method_specs):
            self._proxy = proxy
            self._method_name = method_name
            self._method_specs = method_specs

        def __repr__(self):
            return '{}.{}'.format(repr(self._proxy), self._method_name)

        def __call__(self, **input_kwargs):
            if not PipelineStepContext().in_context:
                raise PipelineError('{} can only be called in a pipeline step context'.format(str(self)))

            input_specs = self._method_specs.get('input', {})
            if set(input_kwargs) != set(input_specs):
                raise PipelineError("arguments to method '{}' do not match method input "
                                    "specifications".format(self._method_name))

            for name, type_ in input_kwargs.items():
                if type_ != input_specs[name]:
                    raise PipelineError("type of argument '{}' to method {} does not match "
                                        "method input specifications".format(name, self._method_name))

            PipelineStepContext().add_method_call_in_context(MethodCall(
                self._proxy, self._method_name, input_kwargs, self._method_specs['output']
            ))
            return self._method_specs['output']


class SourceProxyFactory(AbstractComponentProxyFactory):
    data_type = 'SOURCE'
    component_type = 'sources'

    def __call__(self, **kwargs):
        return super().__call__(**kwargs)

    def __getattr__(self, method_name: str):
        method_specs = self.specs[SPEC_IOP_DECLARATION_KEY].get(method_name, None)
        if method_specs is None:
            raise AttributeError('{} has no output method {}'.format(
                self.specs[SPEC_DEFINITION_KEY]['class'], method_name))

        method_specs['output'] = {k: mezuri_types.get_deserialized(v)
                                  for k, v in method_specs['output'].items()}
        return self.SourceMethodProxy(self, method_name, method_specs)

    class SourceMethodProxy(AbstractComponentProxyFactory.ComponentMethodProxy):
        def __call__(self):
            return super().__call__()


class OperatorProxyFactory(AbstractComponentProxyFactory):
    data_type = 'OPERATOR'
    component_type = 'operators'

    def __call__(self, **kwargs):
        param_specs = self.specs[SPEC_IOP_DECLARATION_KEY]['parameters']
        if set(kwargs.keys()) != set(param_specs):
            raise PipelineError('arguments to __init__ do not match parameter specifications')

        for name, type_ in kwargs.items():
            if type_ != param_specs[name]:
                raise PipelineError("type of argument '{}' does not match parameter "
                                    "specifications".format(name))

        return super().__call__(**kwargs)

    def __getattr__(self, method_name: str):
        method_specs = self.specs[SPEC_IOP_DECLARATION_KEY]['methods'].get(method_name, None)
        if method_specs is None:
            raise AttributeError('{} has no output method {}'.format(
                self.specs[SPEC_DEFINITION_KEY]['class'], method_name))

        method_specs['input'] = {k: mezuri_types.get_deserialized(v)
                                 for k, v in method_specs['input'].items()}
        method_specs['output'] = {k: mezuri_types.get_deserialized(v)
                                  for k, v in method_specs['output'].items()}
        return super().ComponentMethodProxy(self, method_name, method_specs)


class InterfaceProxyFactory(AbstractComponentProxyFactory):
    data_type = 'INTERFACE'
    component_type = 'interfaces'

    def __call__(self, *args, **kwargs):
        return self


class AbstractIOP(metaclass=ABCMeta):
    @property
    @abstractmethod
    def _attr_key(self):
        return NotImplemented

    @property
    @abstractmethod
    def _attr_io_key(self):
        return NotImplemented

    def __init__(self, name: str, type_: mezuri_types.AbstractMezuriSerializable):
        self.name = name
        self.type_ = type_

    def __call__(self, method: Callable):
        setattr(method, self._attr_key, True)

        io = getattr(method, self._attr_io_key, tuple())
        io = ((self.name, self.type_),) + io
        setattr(method, self._attr_io_key, io)
        return method

DECLARATION_ATTR_INPUT_KEY = '__input__'
DECLARATION_ATTR_OUTPUT_KEY = '__output__'
DECLARATION_ATTR_PARAMETER_KEY = '__parameter__'


class Input(AbstractIOP):
    _attr_key = IO_METHOD_DECLARATION_ATTR
    _attr_io_key = DECLARATION_ATTR_INPUT_KEY


class Output(AbstractIOP):
    _attr_key = IO_METHOD_DECLARATION_ATTR
    _attr_io_key = DECLARATION_ATTR_OUTPUT_KEY


class Parameter(AbstractIOP):
    _attr_key = PARAM_METHOD_DECLARATION_ATTR
    _attr_io_key = DECLARATION_ATTR_PARAMETER_KEY


def extract_component_definition(definition_file: str, definition_class: str):
    with open(definition_file) as f:
        contents = f.read()

    globals_ = {}
    exec(contents, globals_)

    return globals_.get(definition_class, None)
