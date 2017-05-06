#!/usr/bin/env python3

from functools import total_ordering
import re


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
        return '/'.join(['mezuri', self.component_type, self.component_name, str(self.version)])

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
