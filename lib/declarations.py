#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from typing import Dict as _Dict


class MezuriType(metaclass=ABCMeta):
    @abstractmethod
    @property
    def type(self):
        return NotImplemented


class BaseType(MezuriType, metaclass=ABCMeta):
    pass


class Int(BaseType):
    type = 'MEZURI_INT'


class UInt(BaseType):
    type = 'MEZURI_UINT'


class Bool(BaseType):
    type = 'MEZURI_BOOL'


class Double(BaseType):
    type = 'MEZURI_DOUBLE'


class String(BaseType):
    type = 'MEZURI_STRING'


class List(MezuriType):
    type = 'MEZURI_LIST'

    def __init__(self, element_type: MezuriType):
        self.element_type = element_type


class Dict(MezuriType):
    type = 'MEZURI_DICT'

    def __init__(self, definition: _Dict[str, MezuriType]):
        self.definition = definition


class Interface:
    def __init__(self, interface_name: str, version_str: str):
        self.interface_name = interface_name
        self.version_str = version_str
