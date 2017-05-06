#!/usr/bin/env python3

import subprocess


class Git:
    """Wrapper for git."""
    @classmethod
    def init(cls):
        return subprocess.check_output(['git', 'init'])

    @classmethod
    def add(cls, filename: str):
        return subprocess.check_output(['git', 'add', filename])

    @classmethod
    def commit(cls, message: str, allow_empty: bool=False):
        cmd = ['git', 'commit',
               '-a',
               '-m', '{}'.format(message)]
        if allow_empty:
            cmd.append('--allow-empty')
        try:
            subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            return None

        return subprocess.check_output(['git', 'rev-parse', 'HEAD'])

    @classmethod
    def show(cls, filename: str, revision: str='HEAD'):
        """Show a file at a given revision. """
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
                                        remote, 'master'],
                                       stderr=subprocess.STDOUT).decode()

    class GitTag:
        @classmethod
        def list(cls):
            return subprocess.check_output(['git', 'tag']).decode().split()

        @classmethod
        def create(cls, name: str, message: str):
            return subprocess.check_output(['git', 'tag',
                                            '-a',
                                            '-m', message,
                                            name])

    tag = GitTag

    class GitRemote:
        @classmethod
        def list(cls):
            return subprocess.check_output(['git', 'remote']).decode().split()

        @classmethod
        def url(cls, remote_name: str):
            return subprocess.check_output(['git', 'remote',
                                            'get-url', remote_name]).decode()

        @classmethod
        def add(cls, remote_name: str, remote_url: str):
            return subprocess.check_output(['git', 'remote',
                                            'add', remote_name, remote_url]).decode()

    remote = GitRemote
