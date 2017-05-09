#!/usr/bin/env python3

from abc import ABCMeta, abstractclassmethod

from lib.declarations import (
    PARAM_METHOD_DECLARATION_ATTR, IO_METHOD_DECLARATION_ATTR,
    DECLARATION_ATTR_INPUT_KEY, DECLARATION_ATTR_OUTPUT_KEY, DECLARATION_ATTR_PARAMETER_KEY
)


class AbstractComponent(metaclass=ABCMeta):
    @abstractclassmethod
    def __extract_spec(self):
        pass


class AbstractOperator(AbstractComponent, metaclass=ABCMeta):
    @classmethod
    def __extract_spec(cls):
        io_specs = {}
        parameters = {}
        for var_name, var in vars(cls).items():
            if getattr(var, IO_METHOD_DECLARATION_ATTR, False):
                io_specs[var_name] = {
                    'input': getattr(var, DECLARATION_ATTR_INPUT_KEY, tuple()),
                    'output': getattr(var, DECLARATION_ATTR_OUTPUT_KEY, tuple())
                }
            elif getattr(var, PARAM_METHOD_DECLARATION_ATTR, False):
                parameters = getattr(var, DECLARATION_ATTR_PARAMETER_KEY)

        return io_specs, parameters


class AbstractInterface(AbstractComponent, metaclass=ABCMeta):
    @classmethod
    def __extract_spec(cls):
        for var_name, var in vars(cls).items():
            if getattr(var, IO_METHOD_DECLARATION_ATTR, False):
                spec = getattr(var, DECLARATION_ATTR_OUTPUT_KEY, tuple())
                io_spec = {
                    'input': spec,
                    'output': spec
                }
                return io_spec


class AbstractSource(AbstractComponent, metaclass=ABCMeta):
    @classmethod
    def __extract_spec(cls):
        for var_name, var in vars(cls).items():
            if getattr(var, IO_METHOD_DECLARATION_ATTR, False):
                spec = getattr(var, DECLARATION_ATTR_OUTPUT_KEY, tuple())
                io_spec = {
                    'output': spec
                }
                return io_spec
