#!/usr/bin/env python3

from argparse import ArgumentParser
from collections import OrderedDict
from os.path import relpath

from lib.declarations import extract_component_definition
from utilities import (
    SPEC_KEY, SPEC_IOP_DECLARATION_KEY,
    SPEC_DEPENDENCIES_KEY, SPEC_DEFINITION_KEY, SPEC_FILENAME
)
from utilities.constructs import Version
from utilities.git import Git
from .utils import (
    get_project_root_by_specification,
    component_context, component_init,
    component_commit, component_publish
)

INTERFACE_COMMAND_HELP = 'Work with interfaces.'

DEFAULT_DEFINITION_FILE = 'interface.py'
DEFINITION_CLASS_REF = '__mezuri_interface__'


def init(_):
    return component_init('interfaces')


def generate(args) -> int:
    filename = args.file if args.file is not None else DEFAULT_DEFINITION_FILE
    definition_cls = extract_component_definition(filename, DEFINITION_CLASS_REF)
    if definition_cls is None:
        print('Could not evaluate interface definition file {}'.format(filename))

    definition_filename = relpath(filename, get_project_root_by_specification())
    cls_name, io_spec, deps = definition_cls._AbstractInterface__extract_spec_and_dependencies()
    with component_context('interfaces') as ctx:
        ctx[SPEC_KEY][SPEC_IOP_DECLARATION_KEY] = OrderedDict(
            (name, type_.serialize()) for name, type_ in io_spec['input'])
        ctx[SPEC_KEY][SPEC_DEPENDENCIES_KEY] = sorted(d.info.json_serialized() for d in deps)
        ctx[SPEC_KEY][SPEC_DEFINITION_KEY] = OrderedDict((
            ('file', definition_filename),
            ('class', cls_name)
        ))

    Git.add(SPEC_FILENAME)
    Git.add(definition_filename)
    return 0


def commit(args):
    return component_commit('interfaces', args.message, Version(args.version) if args.version else None)


def publish(_):
    return component_publish('interfaces')


def add_interface_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an interface.',
                                             description='Initialize an interface.')
    init_parser.set_defaults(command=init)

    # Generate
    generate_parser = command_parsers.add_parser('generate',
                                                 help='Generate the Input specifications from the '
                                                      'interface definition in the specified file.')
    generate_parser.set_defaults(command=generate)
    generate_parser.add_argument('-f', '--file',
                                 help='The interface definition file. If not provided, {} is '
                                      'assumed.'.format(DEFAULT_DEFINITION_FILE))

    # Commit
    commit_parser = command_parsers.add_parser('commit',
                                               help='Commit a new version of the interface.',
                                               description='Commit a new version of the interface')
    commit_parser.set_defaults(command=commit)
    commit_parser.add_argument('message',
                               help='The commit message')
    commit_parser.add_argument('-v', '--version',
                               help='The new version of the operator. This must be greater '
                                    'than the previous version. If not provided, the version listed'
                                    'in {} will be used. '.format(SPEC_FILENAME))

    # Publish
    publish_parser = command_parsers.add_parser('publish',
                                                help='Publish the operator to an online registry.',
                                                description='Publish the operator to an online registry.')
    publish_parser.set_defaults(command=publish)


def main():
    parser = ArgumentParser(prog='interface',
                            description=INTERFACE_COMMAND_HELP)
    add_interface_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
