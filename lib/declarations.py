#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import Dict as _Dict, Callable


PARAM_METHOD_DECLARATION_ATTR = '__mezuri_param_method__'
IO_METHOD_DECLARATION_ATTR = '__mezuri_io_method__'


Serialized = namedtuple('Serialized', ['data_type', 'contents'])
deserializers = {}


def get_deserialized(contents):
    s = Serialized(*contents)
    return deserializers[s.data_type].deserialize(s.contents)


class MezuriSerializableMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        deserializers[dct['data_type']] = cls

        super(MezuriSerializableMeta, cls).__init__(name, bases, dct)


class AbstractMezuriSerializable(metaclass=MezuriSerializableMeta):
    """
    An abstract class for objects that can be serialized and deserialized
    for the purpose of writing out and reading in from a specification file.
    """
    data_type = NotImplemented

    @abstractmethod
    def serialize(self):
        return NotImplemented

    @classmethod
    @abstractmethod
    def deserialize(cls, contents):
        return NotImplemented

    @abstractmethod
    def __repr__(self):
        return NotImplemented


class MezuriBaseType(AbstractMezuriSerializable):
    data_type = 'ABSTRACT_BASE'

    @classmethod
    def serialize(cls):
        return Serialized(cls.data_type, None)

    @classmethod
    def deserialize(cls, _):
        return cls()

    def __repr__(self):
        return self.data_type


class Int(MezuriBaseType):
    data_type = 'INT'


class Bool(MezuriBaseType):
    data_type = 'BOOL'


class Double(MezuriBaseType):
    data_type = 'DOUBLE'


class String(MezuriBaseType):
    data_type = 'STRING'


class List(AbstractMezuriSerializable):
    data_type = 'LIST'

    def __init__(self, element_type: AbstractMezuriSerializable):
        self.element_type = element_type

    def serialize(self):
        return Serialized(self.data_type, self.element_type.serialize())

    @classmethod
    def deserialize(cls, contents: Serialized):
        return cls(get_deserialized(contents))

    def __repr__(self):
        return '[{}]'.format(repr(self.element_type))


class Dict(AbstractMezuriSerializable):
    data_type = 'DICT'

    def __init__(self, definition: _Dict[str, AbstractMezuriSerializable]):
        self.definition = definition

    def serialize(self):
        return Serialized(self.data_type,
                          {k: v.serialize() for k, v in self.definition.items()})

    @classmethod
    def deserialize(cls, contents: _Dict[str, Serialized]):
        return cls({k: get_deserialized(c) for k, c in contents.items()})

    def __repr__(self):
        return '{{{}}}'.format(', '.join('{}: {}'.format(k, repr(v))
                                         for k, v in self.definition.items()))


    def __init__(self, interface_registry: str, interface_name: str, version_str: str):
        self.interface_registry = interface_registry
        self.interface_name = interface_name
        self.version_str = version_str

    def serialize(self):
        return self.data_type, (self.interface_registry, self.interface_name, self.version_str)


class AbstractIOP(metaclass=ABCMeta):
    @property
    @abstractmethod
    def _attr_key(self):
        return NotImplemented

    @property
    @abstractmethod
    def _attr_io_key(self):
        return NotImplemented

    def __init__(self, name: str, type_: MezuriBaseType or InterfaceProxy):
        self.name = name
        self.type_ = type_

    def __call__(self, method: Callable):
        setattr(method, self._attr_key, True)

        io = getattr(method, self._attr_io_key, tuple())
        io += ((self.name, self.type_), )
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
