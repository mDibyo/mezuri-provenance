#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from typing import Dict as _Dict, Callable

from utilities.registry import RegistryClient

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


class AbstractComponentProxyFactory(AbstractMezuriSerializable):
    data_type = 'ABSTRACT_COMPONENT'

    @classmethod
    @property
    @abstractmethod
    def component_type(cls):
        return NotImplemented

    def __init__(self, registry_url: str, name: str, version_str: str):
        self.registry_url = registry_url
        self.name = name
        self.version_str = version_str

        self._spec = None

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.registry_url,
                                       self.name, self.version_str)

    def serialize(self):
        return Serialized(self.data_type, (self.registry_url, self.name, self.version_str))

    @classmethod
    def deserialize(cls, contents):
        registry_url, name, version_str = contents
        return cls(registry_url, name, version_str)

    def _fetch_spec(self) -> Dict:
        registry = RegistryClient(self.registry_url, self.component_type, self.name)
        return registry.get_component_version(self.version_str)['spec']

    @property
    def spec(self) -> Dict:
        if self._spec is None:
            self._spec = self._fetch_spec()
        return self._spec

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class InterfaceProxyFactory(AbstractComponentProxyFactory):
    data_type = 'INTERFACE'
    component_type = 'interfaces'

    class InterfaceProxy():
        def __init__(self, spec, inputs):
            assert set(inputs.keys()) == set(self.spec['iop_declaration'].keys())

            self.spec = spec
            self.cls_name = spec['definition']['class']
            self.inputs = inputs

        def __repr__(self):
            return '{}({})'.format(self.cls_name, ', '.join(self.inputs))

        def __getattr__(self, item):
            return self.inputs[item]

    def __call__(self, **inputs):
        return self.InterfaceProxy(self.spec, inputs)


class OperatorProxyFactory(AbstractComponentProxyFactory):
    data_type = 'OPERATOR'
    component_type = 'operators'

    class OperatorProxy():
        class OperatorMethodProxy():
            def __init__(self, cls_name, method_name, io_specs):
                self.cls_name = cls_name
                self.method_name = method_name
                self._inputs = io_specs['input'].items()
                self._outputs = io_specs['output'].items()

                setattr(self, IO_METHOD_DECLARATION_ATTR, True)
                setattr(self, DECLARATION_ATTR_INPUT_KEY, self._inputs)
                setattr(self, DECLARATION_ATTR_OUTPUT_KEY, self._outputs)

            def __repr__(self):
                return '{}.{}({})'.format(self.cls_name, self.method_name,
                                          ', '.join(name for name, type_ in self._inputs))

            def __call__(self):
                raise NotImplementedError

        def __init__(self, spec, parameters):
            assert set(parameters.keys()) == \
                   set(self.spec['iop_declaration']['parameters'].keys())

            self.spec = spec
            self.cls_name = spec['definition']['class']
            self.parameters = parameters

        def __getattr__(self, item):
            method_io_specs = self.spec['iop_declaration']['methods'].get(item, None)
            if method_io_specs is not None:
                return self.OperatorMethodProxy(self.cls_name, item, method_io_specs)

    def __call__(self, **parameters):
        return self.OperatorProxy(self.spec, parameters)


class AbstractIOP(metaclass=ABCMeta):
    @property
    @abstractmethod
    def _attr_key(self):
        return NotImplemented

    @property
    @abstractmethod
    def _attr_io_key(self):
        return NotImplemented

    def __init__(self, name: str, type_: AbstractMezuriSerializable):
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
