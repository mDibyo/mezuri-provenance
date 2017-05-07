#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict as _Dict, Callable, Type


DECLARATION_ATTR_KEY = '__mezuri_attr__'


class MezuriType(metaclass=ABCMeta):
    @property
    @abstractmethod
    def type(self):
        return NotImplemented


class MezuriBaseType(MezuriType, metaclass=ABCMeta):
    pass


class Int(MezuriBaseType):
    type = 'MEZURI_INT'


class UInt(MezuriBaseType):
    type = 'MEZURI_UINT'


class Bool(MezuriBaseType):
    type = 'MEZURI_BOOL'


class Double(MezuriBaseType):
    type = 'MEZURI_DOUBLE'


class String(MezuriBaseType):
    type = 'MEZURI_STRING'


class List(MezuriType):
    type = 'MEZURI_LIST'

    def __init__(self, element_type: Type[MezuriType]):
        self.element_type = element_type


class Dict(MezuriType):
    type = 'MEZURI_DICT'

    def __init__(self, definition: _Dict[str, MezuriType]):
        self.definition = definition


class MezuriInterface:
    def __init__(self, interface_name: str, version_str: str):
        self.interface_name = interface_name
        self.version_str = version_str


class AbstractIOP(metaclass=ABCMeta):
    _attr_key = DECLARATION_ATTR_KEY

    @property
    @abstractmethod
    def _attr_io_key(self):
        return NotImplemented

    def __init__(self, name: str, type_: MezuriBaseType or MezuriInterface):
        self.name = name
        self.type_ = type_

    def __call__(self, callable_: Callable):
        getattr(callable_, self._attr_key)[self._attr_io_key][self.name] = self.type_
        return callable_


DECLARATION_ATTR_INPUT_KEY = '__input__'
DECLARATION_ATTR_OUTPUT_KEY = '__input__'
DECLARATION_ATTR_PARAMETER_KEY = '__parameter__'


class Input(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_INPUT_KEY


class Output(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_OUTPUT_KEY


class Parameter(AbstractIOP):
    _attr_io_key = DECLARATION_ATTR_PARAMETER_KEY
