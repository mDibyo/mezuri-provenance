#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict as _Dict, Callable


DECLARATION_ATTR = '__mezuri_dcl__'
DECLARATION_CREATE_FUNC_ATTR = '__mezuri_dcl_create_func__'


class MezuriType(metaclass=ABCMeta):
    data_type = NotImplemented

    @abstractmethod
    def serialize(self):
        return NotImplemented


class MezuriBaseType(MezuriType, metaclass=ABCMeta):
    def __init__(self, data_type):
        self.data_type = data_type

    def serialize(self):
        return self.data_type

Int = MezuriBaseType('INT')
Bool = MezuriBaseType('BOOL')
Double = MezuriBaseType('DOUBLE')
String = MezuriBaseType('STRING')


class List(MezuriType):
    data_type = 'LIST'

    def __init__(self, element_type: MezuriType):
        self.element_type = element_type

    def serialize(self):
        return self.data_type, self.element_type.serialize()


class Dict(MezuriType):
    data_type = 'DICT'

    def __init__(self, definition: _Dict[str, MezuriType]):
        self.definition = definition

    def serialize(self):
        return self.data_type, {k: v.serialize() for k, v in self.definition}


class InterfaceProxy:
    data_type = 'INTERFACE'

    def __init__(self, interface_registry: str, interface_name: str, version_str: str):
        self.interface_registry = interface_registry
        self.interface_name = interface_name
        self.version_str = version_str

    def serialize(self):
        return self.data_type, (self.interface_registry, self.interface_name, self.version_str)


class AbstractIOP(metaclass=ABCMeta):
    _attr_key = DECLARATION_ATTR

    @property
    @abstractmethod
    def _attr_io_key(self):
        return NotImplemented

    def __init__(self, name: str, type_: MezuriBaseType or InterfaceProxy):
        self.name = name
        self.type_ = type_

    @staticmethod
    def _initialize_callable(callable_: Callable):
        if not hasattr(callable_, DECLARATION_ATTR):
            setattr(callable_, DECLARATION_ATTR,
                    getattr(callable_, DECLARATION_CREATE_FUNC_ATTR)())

    def __call__(self, callable_: Callable):
        self._initialize_callable(callable_)

        getattr(callable_, self._attr_key)[self._attr_io_key][self.name] = self.type_
        return callable_

DECLARATION_ATTR_INPUT_KEY = '__input__'
DECLARATION_ATTR_OUTPUT_KEY = '__output__'
DECLARATION_ATTR_PARAMETER_KEY = '__parameter__'


class Input(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_INPUT_KEY


class Output(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_OUTPUT_KEY


class Parameter(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_PARAMETER_KEY
