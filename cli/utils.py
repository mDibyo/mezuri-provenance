#!/usr/bin/env python3

from collections import OrderedDict
from contextlib import contextmanager
from functools import total_ordering
import json
import os
import re
import subprocess

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

DEFAULT_VERSION = '0.0.0'
DEFAULT_REGISTRY = 'http://registry.mezuri.org'

component_spec_defaults = {
    'name': None,
    'description': None,
    'version': DEFAULT_VERSION
}


def input_git_remote():
    remote_url = input('Git remote: ')
    remote_name = input('Remote name: ')
    return {
        'name': remote_name,
        'url': remote_url
    }


def input_registry():
    registry = input('registry [{}]: '.format(DEFAULT_REGISTRY)).strip()
    return registry if registry else DEFAULT_VERSION


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
        return json.load(f, object_hook=OrderedDict), filename


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
        with open(context[SPEC_PATH_KEY], 'w') as f:
            json.dump(context[SPEC_KEY], f, indent=4)


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
            print('Component already initialized')
            return 1

        spec = ctx[SPEC_KEY]
        spec['name'] = input('Name: ').strip()
        spec['description'] = input('Description: ').strip()
        version = input('Version ({}): '.format(DEFAULT_VERSION)).strip()
        spec['version'] = version if version else DEFAULT_VERSION

        Git.init()
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPEC_FILENAME)
    Git.add(SPEC_FILENAME)
    return 0


def component_commit(message: str, version: str=None, spec_defaults=None):
    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Component not initialized')
            return 1

        if version is not None:
            ctx[SPEC_KEY]['version'] = version
        current_version = Version(ctx[SPEC_KEY]['version'])
        last_spec_raw = Git.show('HEAD', SPEC_FILENAME)
        if last_spec_raw is not None:
            last_spec = json.loads(last_spec_raw)
            last_version = Version(last_spec['version'])
            if last_version >= current_version:
                print('Version {} not greater than {}'.format(current_version, last_version))
                return 1

    Git.commit(message)
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


class Git:
    """Wrapper for git."""
    @classmethod
    def init(cls):
        return subprocess.check_output(['git', 'init'])

    @classmethod
    def add(cls, filename: str):
        return subprocess.check_output(['git', 'add', filename])

    @classmethod
    def commit(cls, message: str):
        return subprocess.check_output(['git', 'commit',
                                        '-a',
                                        '-m', '{}'.format(message)])

    @classmethod
    def show(cls, revision: str, filename: str):
        try:
            return subprocess.check_output(['git', 'show',
                                            '{}:{}'.format(revision, filename)],
                                           stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                return None
            raise

    @classmethod
    def push(cls, remote: str):
        return subprocess.check_output(['git', 'push',
                                        remote, 'master'])

    class GitRemote:
        @classmethod
        def list(cls):
            return subprocess.check_output(['git', 'remote']).decode().split()

        @classmethod
        def url(cls, remote_name: str):
            return subprocess.check_output(['git', 'remote',
                                            'get-url', remote_name]).decode()

    remote = GitRemote


class Registry:
    def __init__(self, url: str):
        self.url = url

    def push(self, component_type, component_name):
        pass


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
