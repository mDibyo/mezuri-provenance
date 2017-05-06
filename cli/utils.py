#!/usr/bin/env python3

from collections import OrderedDict
from contextlib import contextmanager
from functools import total_ordering
import json
import os
import re
from typing import Dict

from utilities.git import Git


@total_ordering
class Version:
    """Version represents a semantic version of an entity."""

    version_regex = re.compile(r'(\d).(\d).(\d)')

    def __init__(self, version_str: str):
        match = self.version_regex.fullmatch(version_str)
        if match is None:
            raise RuntimeError('"{}" is not a valid version.'.format(version_str))

        self.major_number, self.minor_number, self.patch_number = map(int, match.groups())

    def __repr__(self):
        return '{}.{}.{}'.format(self.major_number, self.minor_number, self.patch_number)

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

DEFAULT_VERSION = Version('0.0.0')


@total_ordering
class VersionTag:
    """VersionTags have the format "mezuri/{component_type}/{component_name}/{version}".  """

    def __init__(self, component_type: str, component_name: str, version: Version):
        self.component_type = component_type
        self.component_name = component_name
        self.version = version

    @classmethod
    def parse(cls, version_tag_str: str) -> 'VersionTag':
        _, component_type, component_name, version_str = version_tag_str.split('/')
        return cls(component_type, component_name, Version(version_str))

    def __repr__(self):
        return '/'.join(['mezuri', self.component_type, self.component_name, self.version])

    @staticmethod
    def _is_valid_version(other):
        return type(other) == VersionTag

    def __eq__(self, other: 'VersionTag'):
        if (self.component_type != other.component_type or
                    self.component_name != other.component_name):
            return False

        return self.version == other.version

    def __gt__(self, other: 'VersionTag'):
        if (self.component_type != other.component_type or
                self.component_name != other.component_name):
            return NotImplemented

        return self.version > other.version

"""
Utilities for CLI.

specification.json format:
{
    "name": <component name>,
    "description": <component description>,
    "version": "0.0.0",
    "publish": {
        "remote": {
            "name": <remote name>,
            "url": <remote url>
        }
        "registry": <registry url>
    }
}
"""
SPEC_KEY = 'spec'
SPEC_PATH_KEY = 'specPath'
SPEC_FILENAME = 'specification.json'

DEFAULT_REGISTRY = 'http://registry.mezuri.org'

TAG_NAME_FORMAT = 'mezuri/{component_type}/{version}'

component_spec_defaults = OrderedDict((
    ('name', None),
    ('description', None),
    ('version', DEFAULT_VERSION)
))


def input_name() -> str:
    name = input('Name (only a-z,-): ').strip()
    while len(name.split()) > 1:
        print('{} is not a valid Component name. Try again.'.format(name))
        name = input('Name (only a-z,-): ').strip()
    return name


def input_git_remote() -> Dict:
    remote_url = input('Git remote: ')
    remote_name = input('Remote name: ')
    return {
        'name': remote_name,
        'url': remote_url
    }


def input_registry() -> str:
    registry = input('registry [{}]: '.format(DEFAULT_REGISTRY)).strip()
    return registry if registry else DEFAULT_REGISTRY


def get_project_root_by_specification():
    directory = os.getcwd()
    while True:
        if os.path.exists(os.path.join(directory, SPEC_FILENAME)):
            return directory

        if directory == '/':
            return None

        directory = os.path.abspath(os.path.join(directory, os.path.pardir))


def specification_filename():
    project_root = get_project_root_by_specification()
    if project_root is None:
        return None

    return os.path.join(project_root, SPEC_FILENAME)


def specification():
    """Returns specifications and path to specifications."""
    filename = specification_filename()
    if filename is None:
        return None, None

    with open(filename) as f:
        spec = json.load(f, object_pairs_hook=OrderedDict)

    spec['version'] = Version(spec['version'])
    return spec, filename


def calculate_component_context(spec_defaults=None):
    spec = component_spec_defaults.copy()
    if spec_defaults is not None:
        spec.update(spec_defaults)
    context = {SPEC_KEY: spec}

    saved_spec, path = specification()
    if saved_spec is not None:
        context[SPEC_KEY].update(saved_spec)
        context[SPEC_PATH_KEY] = path

    return context


def save_component_context(context):
    if SPEC_PATH_KEY in context:
        spec_to_save = OrderedDict()
        for k, v in context[SPEC_KEY].items():
            if type(v) == Version:
                v = str(v)
            spec_to_save[k] = str(v)

        with open(context[SPEC_PATH_KEY], 'w') as f:
            json.dump(spec_to_save, f, indent=4)


@contextmanager
def component_context(spec_defaults=None):
    ctx = calculate_component_context(spec_defaults)
    try:
        yield ctx
    finally:
        save_component_context(ctx)


def component_init(spec_defaults=None):
    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY in ctx:
            # TODO(dibyo): Support initializing/re-initializing from passed in
            # JSON-file
            print('Component already initialized.')
            return 1

        spec = ctx[SPEC_KEY]
        spec['name'] = input_name()
        spec['description'] = input('Description: ').strip()
        version = input('Version [{}]: '.format(DEFAULT_VERSION)).strip()
        spec['version'] = Version(version) if version else DEFAULT_VERSION

        Git.init()
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPEC_FILENAME)
    Git.add(SPEC_FILENAME)
    return 0


def component_commit(component_type: str, message: str, version: Version=None, spec_defaults=None):
    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Component not initialized')
            return 1

        current_version = version if version is not None else ctx[SPEC_KEY]['version']

        # Check if version has been incremented.
        version_tag = VersionTag(component_type, ctx[SPEC_KEY]['name'], current_version)
        prev_tags = map(VersionTag.parse, Git.tag.list())
        if prev_tags:
            last_tag = max(prev_tags)
            if version_tag <= last_tag:
                print('Version {} not greater than {}'.format(current_version, last_tag.version))
                return 1

        ctx[SPEC_KEY]['version'] = current_version

    Git.commit(message)
    Git.tag.create(str(version_tag), message)
    return 0


def component_publish(component_type: str, spec_defaults=None):
    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Component in not initialized')
            return 1

        spec = ctx[SPEC_KEY]
        if 'publish' not in spec:  # Component has never been published before.
            remote_names = Git.remote.list()
            if not remote_names:
                remote = input_git_remote()
            else:
                remote_name = input('Git remote [{}]: '.format(', '.join(remote_names))).strip()
                if remote_name:
                    remote = {
                        'name': remote_name,
                        'url': Git.remote.url(remote_name)
                    }
                else:
                    remote = input_git_remote()

            registry = input_registry()
            spec['publish'] = {
                'remote': remote,
                'registry': registry
            }

        publish = spec['publish']
        Git.push(publish['remote']['name'])
        Registry(publish['registry']).push(component_type, spec['name'])


class Registry:
    def __init__(self, url: str):
        self.url = url

    def push(self, component_type, component_name):
        pass
