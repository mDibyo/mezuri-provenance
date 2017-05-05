#!/usr/bin/env python3

from collections import OrderedDict
from functools import total_ordering
import json
import os
import re
import subprocess

SPECIFICATION_FILE = 'specification.json'


def get_project_root_by_specification():
    directory = os.getcwd()
    while True:
        if os.path.exists(os.path.join(directory, SPECIFICATION_FILE)):
            return directory

        if directory == '/':
            return None

        directory = os.path.abspath(os.path.join(directory, os.path.pardir))


def specification_filename():
    project_root = get_project_root_by_specification()
    if project_root is None:
        return None

    return os.path.join(project_root, SPECIFICATION_FILE)


def get_specification():
    """Returns specifications and path to specifications."""
    filename = specification_filename()
    if filename is None:
        return None, None

    with open(filename) as f:
        return json.load(f, object_hook=OrderedDict), filename


class Git:
    """Wrapper for git."""
    @classmethod
    def init(cls):
        return subprocess.check_output(['git', 'init'])

    @classmethod
    def add(cls, filename):
        return subprocess.check_output(['git', 'add', filename])

    @classmethod
    def commit(cls, message):
        return subprocess.check_output(['git', 'commit',
                                        '-a',
                                        '-m', '{}'.format(message)])

    @classmethod
    def show(cls, revision: str, filename: str):
        try:
            return subprocess.check_output(['git', 'show',
                                            '{}:{}'.format(revision, filename)],
                                           stderr=subprocess.STDOUT).decode('utf-8')
        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                return None
            raise


@total_ordering
class Version:
    """Version represents a semantic version of an entity."""

    version_regex = re.compile(r'(\d).(\d).(\d)')

    def __init__(self, version_str: str):
        match = self.version_regex.fullmatch(version_str)
        if match is None:
            raise RuntimeError('Invalid version {}.'.format(version_str))

        self.major_number, self.minor_number, self.patch_number = map(int, match.groups())

    def __str__(self):
        return 'v{}.{}.{}'.format(self.major_number, self.minor_number, self.patch_number)

    @staticmethod
    def _is_valid_version(other):
        return (hasattr(other, 'major_number') and
                hasattr(other, 'minor_number') and
                hasattr(other, 'patch_number'))

    def __eq__(self, other: 'Version'):
        if not self._is_valid_version(other):
            return NotImplemented

        return (self.major_number == other.major_number and
                self.minor_number == other.minor_number and
                self.patch_number == other.patch_number)

    def __gt__(self, other: 'Version'):
        if not self._is_valid_version(other):
            return NotImplemented

        if self.major_number > other.major_number:
            return True

        if self.minor_number > other.minor_number:
            return True

        return self.patch_number > other.patch_number
