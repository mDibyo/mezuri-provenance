#!/usr/bin/env python3

import json
import os
import subprocess

SPECIFICATION_FILE = 'specification.json'


def get_specification():
    """Returns specifications and path to specifications."""
    directory = os.getcwd()
    while True:
        path = os.path.join(directory, SPECIFICATION_FILE)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f), path

        if directory == '/':
            return None, ''

        directory = os.path.abspath(os.path.join(directory, os.path.pardir))


class Git:
    """Wrapper for git."""
    @classmethod
    def init(cls):
        return subprocess.check_call(['git', 'init'])
