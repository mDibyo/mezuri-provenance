#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import Dict as DictType


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

    @property
    @abstractmethod
    def dependencies(self):
        return NotImplemented

    @abstractmethod
    def __repr__(self):
        return NotImplemented

    @abstractmethod
    def __eq__(self, other: 'AbstractMezuriSerializable'):
        return NotImplemented


class MezuriBaseType(AbstractMezuriSerializable):
    data_type = 'ABSTRACT_BASE'

    def serialize(self):
        return Serialized(self.data_type, None)

    @classmethod
    def deserialize(cls, _):
        return cls()

    @property
    def dependencies(self):
        return set()

    def __repr__(self):
        return self.data_type

    def __eq__(self, other):
        return self.data_type == other.data_type


class Int(MezuriBaseType):
    data_type = 'INT'


class Bool(MezuriBaseType):
    data_type = 'BOOL'


class Double(MezuriBaseType):
    data_type = 'DOUBLE'


class Datetime(MezuriBaseType):
    data_type = 'DATETIME'


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

    @property
    def dependencies(self):
        return self.element_type.dependencies

    def __repr__(self):
        return '[{}]'.format(repr(self.element_type))

    def __eq__(self, other):
        return (self.data_type == other.data_type and
                self.element_type == other.element_type)


class Dict(AbstractMezuriSerializable):
    data_type = 'DICT'

    def __init__(self, definition: DictType[str, AbstractMezuriSerializable]):
        self.definition = definition

    def serialize(self):
        return Serialized(self.data_type,
                          {k: v.serialize() for k, v in self.definition.items()})

    @classmethod
    def deserialize(cls, contents: DictType[str, Serialized]):
        return cls({k: get_deserialized(c) for k, c in contents.items()})

    @property
    def dependencies(self):
        deps = set()
        for c in self.definition.values():
            deps |= c.dependencies
        return deps

    def __repr__(self):
        return '{{{}}}'.format(', '.join('{}: {}'.format(k, repr(v))
                                         for k, v in self.definition.items()))

    def __eq__(self, other):
        return (self.data_type == other.data_type and
                self.definition == other.definition)
