#!/usr/bin/env python3

import requests

from utilities.constructs import VersionTag


class RegistryError(BaseException):
    pass


class RegistryClient:
    def __init__(self, url: str, component_type: str, component_name: str=None):
        self.url = url
        self.component_type = component_type
        self.component_name = component_name

    @property
    def components_url(self):
        return '/'.join([self.url, self.component_type])

    @property
    def component_url(self):
        if self.component_name is None:
            raise RuntimeError('Component name not provided.')

        return '/'.join([self.url, self.component_type, self.component_name])

    @property
    def versions_url(self):
        if self.component_name is None:
            raise RuntimeError('Component name not provided.')

        return '/'.join([self.url, self.component_type, self.component_name, 'versions'])

    def version_url(self, version: str):
        if self.component_name is None:
            raise RuntimeError('Component name not provided.')

        return '/'.join([self.url, self.component_type, self.component_name, 'versions', version])

    def get_component(self):
        response = requests.get(self.component_url, timeout=None)
        if response.status_code == requests.codes.ok:
            return response.json()['component']
        return None

    def post_component(self, git_remote_url: str):
        if self.component_name is None:
            raise RuntimeError('Component name not provided.')

        response = requests.post(self.components_url, json={
            'name': self.component_name,
            'gitRemoteUrl': git_remote_url,
        }, timeout=None)
        if response.status_code == requests.codes.created:
            return response.json()['component']
        raise RegistryError('Component {} could not be added: {}'.format(
            self.component_name, response.json()['error']))

    def get_component_versions(self):
        response = requests.get(self.versions_url, timeout=None)
        if response.status_code == requests.codes.ok:
            return response.json()['versions']
        return None

    def get_component_version(self, version: str):
        response = requests.get(self.version_url(version), timeout=None)
        if response.status_code == requests.codes.ok:
            return response.json()['componentVersion']
        return None

    def post_component_version(self, version: str, version_tag: str, version_hash: str):
        response = requests.post(self.versions_url, json={
            'version': version,
            'version_tag': version_tag,
            'version_hash': version_hash
        }, timeout=None)
        if response.status_code == requests.codes.created:
            return response.json()['componentVersion']
        raise RegistryError('Component version {} could not be added: {}'.format(
            version, response.json()['error']))

    def push(self, remote_url: str, version_tag: VersionTag, version_hash: str):
        version_str = str(version_tag.version)
        component = self.get_component()
        if component is None:
            self.post_component(remote_url)

        component_versions = self.get_component_versions()
        assert component_versions is not None
        for component_version in component_versions:
            if component_version['version'] == version_str:
                break
        else:
            self.post_component_version(version_str, str(version_tag), version_hash)
