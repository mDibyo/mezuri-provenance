#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import relpath

from lib.declarations import DECLARATION_ATTR_INPUT_KEY, DECLARATION_ATTR_OUTPUT_KEY, DECLARATION_ATTR_PARAMETER_KEY
from utilities.constructs import Version
from .utils import (
    SPEC_FILENAME, SPEC_KEY, get_project_root_by_specification,
    component_context, component_init, extract_component_declaration,
    component_commit, component_publish
)

INTERFACE_COMMAND_HELP = 'Work with interfaces.'

DEFAULT_DEFINITION_FILE = 'interface.py'


def init(_):
    return component_init()


def generate(args):
    filename = args.file if args.file is not None else DEFAULT_DEFINITION_FILE
    decl = extract_component_declaration(filename, 'Interface')
    if decl is None:
        print('Could not evaluate operator definition file {}'.format(filename))

    with component_context() as ctx:
        ctx[SPEC_KEY]['iop_declaration'] = {
            'inputs': {k: v.serialize() for k, v in decl[DECLARATION_ATTR_INPUT_KEY].items()},
        }
        ctx[SPEC_KEY]['definition'] = relpath(filename, get_project_root_by_specification())
    return 0


def commit(args):
    return component_commit('interface', args.message, Version(args.version) if args.version else None)


def publish():
    return component_publish('interface')


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
