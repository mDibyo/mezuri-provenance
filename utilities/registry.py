#!/usr/bin/env python3

import requests


class RegistryClient:
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

    def get(self):
        response = requests.get(self.component_url, timeout=None)
        if response.status_code == 200:
            return response.json()['component']
        return None

    def push(self, remote_url: str, tag: str):
        component = self.get()
        print(component)
        if component is None:  # Component already exists.
            response = requests.post(self.components_url, json={
                'name': self.component_name,
                'gitRemoteUrl': remote_url,
                'tag': tag
            }, timeout=None)
            print(response.json())
