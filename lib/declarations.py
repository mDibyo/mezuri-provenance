#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict, Callable

import lib.types as mezuri_types
from utilities import ComponentInfo
from utilities.registry import RegistryClient

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

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.registry_url,
                                       self.name, self.version_str)

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

    def _fetch_spec(self) -> Dict:
        registry = RegistryClient(self.registry_url, self.component_type, self.name)
        return registry.get_component_version(self.version_str)['specs']

    @property
    def specs(self) -> Dict:
        if self._specs is None:
            self._specs = self._fetch_spec()
        return self._specs

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class SourceProxyFactory(AbstractComponentProxyFactory):
    data_type = 'SOURCE'
    component_type = 'sources'

    def __call__(self, *args, **kwargs):
        return self


class OperatorProxyFactory(AbstractComponentProxyFactory):
    data_type = 'OPERATOR'
    component_type = 'operators'

    def __call__(self, *args, **kwargs):
        return self


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
        io = ((self.name, self.type_), ) + io
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
    try:
        exec(contents, globals_)
    except Exception:
        return None

    return globals_.get(definition_class, None)
