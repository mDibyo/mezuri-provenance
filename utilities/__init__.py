#!/usr/bin/env python3

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
