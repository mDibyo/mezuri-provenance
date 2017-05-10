#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod
import csv
from typing import Optional, Callable, Dict, Generic, TypeVar, Sequence

from lib.declarations import (
    PARAM_METHOD_DECLARATION_ATTR, IO_METHOD_DECLARATION_ATTR,
    DECLARATION_ATTR_INPUT_KEY, DECLARATION_ATTR_OUTPUT_KEY, DECLARATION_ATTR_PARAMETER_KEY
)


class AbstractComponent(metaclass=ABCMeta):
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

        return cls.__name__, io_specs, parameters


class AbstractInterface(AbstractComponent, metaclass=ABCMeta):
    """
        Class from which all Interfaces must be sub-classed.  It contains the
        machinery required by the mezuri CLI to generate corresponding declaration
        for the component definition.

        Interfaces must take all constituent data_types as Inputs to the `__init__` 
        method as follows:
        ```
        from .declarations import Input

        class Interface(AbstractInterface):
            @Input('data1', DataType1)
            @Input('data2', DataType2)
            def __init__(self):
                ...
        ```
    """

    @classmethod
    def __extract_spec(cls):
        """
        Extract specifications for this interface.

        This method is part of the internal API and is not meant to be used
        by end-users.
        """
        for var_name, var in vars(cls).items():
            if getattr(var, IO_METHOD_DECLARATION_ATTR, False):
                spec = getattr(var, DECLARATION_ATTR_INPUT_KEY, tuple())
                io_spec = {
                    'input': spec,
                }
                return cls.__name__, io_spec


class AbstractSource(AbstractComponent, metaclass=ABCMeta):
    """
    Class from which all Sources must be sub-classed.  It contains the
    machinery required by the mezuri CLI to generate corresponding declaration
    for the component definition.

    Sources must NOT take any arguments to the `__init__` method.
    Sources can define a number of output methods which must have the following
    signature:
    ```
    from typing import TypeVar

    from .declarations import Output

    SourceReader = TypeVar('SourceReader', bound=AbstractSourceReader)

    class Source(AbstractSource):
        @Output('output1', OutputType1)
        @Output('output2', OutputType2)
        def method_name(self) -> SourceReader:
            ...
    ```    
    """

    @classmethod
    def __extract_spec(cls):
        """
        Extract specifications for this source.

        This method is part of the internal API and is not meant to be used
        by end-users.
        """
        specs = {}
        cls_inst = cls()
        for var_name, var in vars(cls).items():
            if hasattr(var, '__get__'):
                bound_var = var.__get__(cls_inst, cls)
                if getattr(bound_var, IO_METHOD_DECLARATION_ATTR, False):
                    reader = bound_var()
                    specs[var_name] = {
                        'output': getattr(bound_var, DECLARATION_ATTR_OUTPUT_KEY, tuple()),
                        'uri': reader.uri,
                        'query': reader.query
                    }

        return cls.__name__, specs


SourceOutput = TypeVar('SourceOutput')


class AbstractSourceReader(Generic[SourceOutput], metaclass=ABCMeta):
    """
    Class from which all SourceReaders must inherit. It contains a number of
    methods/attributes that readers must supply in order for the mezuri CLI to
    obtain source output and generate definitions.
    """

    @property
    @abstractmethod
    def uri(self):
        """
        Stores the URI to the file/database that this source represents.  For
        example:
        - a CSV file source: file://relative/path/to/file
        - a MySQL database query: mysql://database
        """
        pass

    @uri.setter
    def uri(self, _):
        pass

    @property
    @abstractmethod
    def query(self):
        """
        Stores the query to be run on that file or database to get the output.
        This query must be understandable by the read method of this class.
        """
        pass

    @query.setter
    def query(self, _):
        pass

    def __repr__(self):
        return '{}({}:{})'.format(self.__class__.__name__, self.uri, self.query)

    @abstractmethod
    def read(self, query: str) -> Sequence[SourceOutput]:
        """
        Calculates and returns the output for this source based on the query.
        """
        pass


class CSVFileReader(AbstractSourceReader):
    query = 'read'

    def __init__(self, filename, field_mapper: Optional[Callable[[Dict], SourceOutput]]=None):
        """
        Read a CSV file.

        :param filename: the relative path to the file being read.
        :param field_mapper: the function that maps fields for each input line
            to the output.
        """
        self.filename = filename
        self.field_mapping = field_mapper

    @property
    def uri(self):
        return 'file://{}'.format(self.filename)

    @staticmethod
    def _file_iterator(filename: str):
        """
        Return a line iterator for the filename.  This lazily opens the file
        when required and keep the file open until all lines have been
        consumed.

        :param filename: the relative path to the file being read.
        """
        with open(filename) as f:
            for line in f:
                yield line

    def read(self, query: str='read'):
        csv_reader = csv.DictReader(self._file_iterator(self.filename))
        if self.field_mapping is None:
            return csv_reader
        return map(self.field_mapping, csv_reader)
