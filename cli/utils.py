#!/usr/bin/env python3

from collections import OrderedDict
from contextlib import contextmanager
import json
import os
import requests
from typing import Dict

from lib.declarations import DECLARATION_ATTR
from utilities.git import Git
from utilities.constructs import Version, DEFAULT_VERSION, VersionTag

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
    remote_url = input('Git remote url: ').strip()
    remote_name = input('Git remote name: ').strip()
    return {
        'name': remote_name,
        'url': remote_url
    }


def input_registry() -> str:
    registry = input('registry [{}]: '.format(DEFAULT_REGISTRY)).strip()
    return registry if registry else DEFAULT_REGISTRY


def get_project_root_by_specification() -> str or None:
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
            spec_to_save[k] = v

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


def extract_component_declaration(definition_file: str, definition_class: str):
    with open(definition_file) as f:
        contents = f.read()

    globals_ = {}
    try:
        exec(contents, globals_)
    except Exception:
        return None

    return getattr(globals_[definition_class], DECLARATION_ATTR)


def component_commit(component_type: str, message: str, version: Version=None, spec_defaults=None):
    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Component not initialized.')
            return 1

        spec = ctx[SPEC_KEY]

        # Check if IOP declaration has been added.
        if 'iop_declaration' not in spec:
            print('Component IOP declaration not added.')
            return 1

        # Check if version has been incremented.
        current_version = version if version is not None else spec['version']
        version_tag = VersionTag(component_type, spec['name'], current_version)
        prev_tags_raw = Git.tag.list()
        if prev_tags_raw:
            last_tag = max(VersionTag.parse(tag) for tag in prev_tags_raw)
            if version_tag <= last_tag:
                print('Version {} not greater than {}'.format(current_version, last_tag.version))
                return 1

        spec['version'] = current_version

    Git.add(spec['definition'])
    Git.commit(message)
    Git.tag.create(str(version_tag), message)
    return 0


def component_publish(component_type: str, spec_defaults=None):
    tags = Git.tag.list()
    if not tags:
        print('Component does not have any versions to publish.')
        return 1
    tag_to_publish = max(VersionTag.parse(tag) for tag in tags)

    with component_context(spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Component in not initialized.')
            return 1

        spec = ctx[SPEC_KEY]
        if 'publish' not in spec:  # Component has never been published before.
            remote_names = Git.remote.list()
            if not remote_names:
                remote = input_git_remote()
                Git.remote.add(remote['name'], remote['url'])
            else:
                remote_name = input('Git remote [{}]: '.format(', '.join(remote_names))).strip()
                if remote_name:
                    remote = {
                        'name': remote_name,
                        'url': Git.remote.url(remote_name)
                    }
                else:
                    remote = input_git_remote()
                    Git.remote.add(remote['name'], remote['url'])

            registry = input_registry()
            spec['publish'] = {
                'remote': remote,
                'registry': registry
            }

        publish = spec['publish']
        Git.push(publish['remote']['name'])
        Registry(publish['registry'], component_type, spec['name']).push(publish['remote']['url'],
                                                                         str(tag_to_publish))


class Registry:
    def __init__(self, url: str, component_type: str, component_name: str):
        self.url = url
        self.component_type = component_type
        self.component_name = component_name

    @property
    def component_url(self):
        return '/'.join([self.url, self.component_type, self.component_name])

    @property
    def components_url(self):
        return '/'.join([self.url, self.component_type])

    def push(self, remote_url: str, tag: str):
        # Check if component already exists
        response = requests.get(self.component_url, timeout=None)
        if response.status_code == 200:  # Component already exists.
            print(response.json())
        else:
            response = requests.post(self.components_url, json={
                'name': self.component_name,
                'gitRemoteUrl': remote_url,
                'tag': tag
            }, timeout=None)
            print(response.json())

