#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import TypeVar

from lib.declarations import (
    DECLARATION_ATTR_KEY,
    DECLARATION_ATTR_INPUT_KEY, DECLARATION_ATTR_OUTPUT_KEY, DECLARATION_ATTR_PARAMETER_KEY
)


OperatorType = TypeVar('OperatorType', bound='AbstractOperator')


class AbstractOperator(metaclass=ABCMeta):
    def __new__(cls, *args, **kwargs):
        setattr(cls, DECLARATION_ATTR_KEY, {
            DECLARATION_ATTR_INPUT_KEY: OrderedDict(),
            DECLARATION_ATTR_OUTPUT_KEY: OrderedDict(),
            DECLARATION_ATTR_PARAMETER_KEY: OrderedDict()
        })

        return super(*args, **kwargs)

    @abstractmethod
    def __init__(
        self,
        **parameters: 'getattr(OperatorType, DECLARATION_ATTR_KEY)[DECLARATION_ATTR_PARAMETER_KEY]'
    ):
        pass

    @abstractmethod
    def __call__(
        self,
        **inputs: 'getattr(OperatorType, DECLARATION_ATTR_KEY)[DECLARATION_ATTR_INPUT_KEY]'
    ) -> 'getattr(OperatorType, DECLARATION_ATTR_KEY)[DECLARATION_ATTR_OUTPUT_KEY]':
        pass


InterfaceType = TypeVar('InterfaceType', bound='AbstractInterface')


class AbstractInterface(metaclass=ABCMeta):
    def __new__(cls, *args, **kwargs):
        setattr(cls, DECLARATION_ATTR_KEY, {
            DECLARATION_ATTR_INPUT_KEY: OrderedDict(),
        })

        return super(*args, **kwargs)

    def __init__(
        self,
        **interface: 'getattr(InterfaceType, DECLARATION_ATTR_KEY)[DECLARATION_ATTR_INPUT_KEY]'
    ) -> None:
        pass


SourceType = TypeVar('SourceType', bound='AbstractSource')


class AbstractSource(metaclass=ABCMeta):
    def __new__(cls, *args, **kwargs):
        setattr(cls, DECLARATION_ATTR_KEY, {
            DECLARATION_ATTR_OUTPUT_KEY: OrderedDict()
        })

        return super(*args, **kwargs)

    def __call__(self) -> 'getattr(SourceType, DECLARATION_ATTR_KEY)[DECLARATION_ATTR_OUTPUT_KEY]':
        pass
