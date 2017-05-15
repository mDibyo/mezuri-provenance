#!/usr/bin/env python3

import os
import subprocess


GIT_NAME = 'Mezuri Provenance'
GIT_EMAIL = 'provenance@mezuri.org'


class Git:
    """Wrapper for git."""
    @classmethod
    def init(cls):
        return subprocess.check_output(['git', 'init'])

    @classmethod
    def clone(cls, url: str, directory: str=None) -> bool:
        cmd = ['git', 'clone',
               url]
        if directory is not None:
            cmd.append(directory)
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError as e:
            if e.returncode == 128:
                return False
            raise

    @classmethod
    def checkout(cls, reference):
        return subprocess.check_output(['git', 'checkout', reference], stderr=subprocess.STDOUT)

    @classmethod
    def add(cls, filename: str):
        return subprocess.check_output(['git', 'add', filename])

    @classmethod
    def rev_parse(cls, obj: str):
        return subprocess.check_output(['git', 'rev-parse', obj]).decode().strip()

    @classmethod
    def commit(cls, message: str, allow_empty: bool=False, substitute_author: bool=False):
        os.putenv('GIT_COMMITTER_NAME', GIT_NAME)
        os.putenv('GIT_COMMITTER_EMAIL', GIT_EMAIL)

        cmd = ['git', 'commit',
               '-a',
               '-m', '{}'.format(message)]
        if allow_empty:
            cmd.append('--allow-empty')
        if substitute_author:
            cmd.extend(['--author', '{} <{}>'.format(GIT_NAME, GIT_EMAIL)])

        try:
            subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            return None

        return cls.rev_parse('HEAD')

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
    def push(cls, remote: str, reference: str='master'):
        try:
            subprocess.check_output(['git', 'push',
                                     remote, reference],
                                    stderr=subprocess.STDOUT).decode()
            return True
        except subprocess.CalledProcessError:
            return False

    class GitTag:
        @classmethod
        def list(cls):
            return subprocess.check_output(['git', 'tag']).decode().split()

        @classmethod
        def create(cls, name: str, message: str):
            subprocess.check_output(['git', 'tag',
                                     '-a',
                                     '-m', message,
                                     name])

            return cls.hash(name)

        @classmethod
        def hash(cls, name: str):
            return Git.rev_parse(name)

        @classmethod
        def message(cls, name: str):
            result = subprocess.check_output(['git', 'tag',
                                              '-l',
                                              '-n',
                                              name]).decode()
            return ' '.join(result.split(' ')[1:])

    tag = GitTag

    class GitRemote:
        @classmethod
        def list(cls):
            return subprocess.check_output(['git', 'remote']).decode().split()

        @classmethod
        def url(cls, remote_name: str):
            return subprocess.check_output(['git', 'remote',
                                            'get-url', remote_name]).decode().strip()

        @classmethod
        def add(cls, remote_name: str, remote_url: str):
            return subprocess.check_output(['git', 'remote',
                                            'add', remote_name, remote_url]).decode()

    remote = GitRemote
