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
        return subprocess.check_output(cmd)

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

    remote = GitRemote
