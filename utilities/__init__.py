#!/usr/bin/env python3

from collections import namedtuple, OrderedDict
from contextlib import contextmanager
import os
from shutil import rmtree
from tempfile import mkdtemp


SPEC_FILENAME = 'specification.json'

SPEC_KEY = 'spec'
SPEC_PATH_KEY = 'specPath'
SPEC_IOP_DECLARATION_KEY = 'iopDeclaration'
SPEC_DEPENDENCIES_KEY = 'dependencies'
SPEC_DEFINITION_KEY = 'definition'


class ComponentInfo(namedtuple('ComponentInfo', ['component_type', 'registry_url',
                                                 'component_name', 'component_version'])):
    @staticmethod
    def _underscore_to_camelcase(value):
        def camelcase():
            yield str.lower
            while True:
                yield str.capitalize

        c = camelcase()
        return "".join(next(c)(x) if x else '_' for x in value.split("_"))

    def json_serialized(self):
        return OrderedDict((self._underscore_to_camelcase(k), v)
                           for k, v in self._asdict().items())


@contextmanager
def temporary_dir(delete :bool=True):
    directory = mkdtemp()
    yield directory
    if delete:
        rmtree(directory)


@contextmanager
def working_dir(directory: str):
    current_directory = os.getcwd()

    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(current_directory)
