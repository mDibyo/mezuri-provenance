#!/usr/bin/env python3

from argparse import ArgumentParser
from collections import OrderedDict
from os.path import relpath

from lib.declarations import extract_component_definition
from utilities.constructs import Version
from utilities.git import Git
from .utils import (
    SPEC_FILENAME, SPEC_KEY, get_project_root_by_specification,
    component_context, component_init,
    component_commit, component_publish
)

OPERATOR_COMMAND_HELP = 'Work with operators.'

DEFAULT_DEFINITION_FILE = 'operator.py'
DEFINITION_CLASS_REF = '__mezuri_operator__'


def init(_) -> int:
    return component_init()


def generate(args) -> int:
    definition_cls = extract_component_definition(args.file, DEFINITION_CLASS_REF)
    if definition_cls is None:
        print('Could not evaluate operator definition file {}'.format(args.file))

    definition_filename = relpath(args.file, get_project_root_by_specification())
    io_specs, parameters = definition_cls._AbstractOperator__extract_spec()
    with component_context() as ctx:
        ctx[SPEC_KEY]['iop_declaration'] = OrderedDict((
            ('parameters', parameters),
            ('io_specs', OrderedDict(
                [(io_method, OrderedDict((
                    ('input', OrderedDict((name, type_.serialize())
                                          for name, type_ in io_specs[io_method]['input'])),
                    ('output', OrderedDict((name, type_.serialize())
                                           for name, type_ in io_specs[io_method]['output']))
                ))) for io_method in sorted(io_specs.keys())]
            ))
        ))
        ctx[SPEC_KEY]['definition'] = definition_filename

    Git.add(SPEC_FILENAME)
    Git.add(definition_filename)
    return 0


def commit(args) -> int:
    return component_commit('operators', args.message, Version(args.version) if args.version else None)


def publish(_):
    return component_publish('operators')


def add_operator_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an operator.',
                                             description='Initialize an operator.')
    init_parser.set_defaults(command=init)

    # Generate
    generate_parser = command_parsers.add_parser('generate',
                                                 help='Generate the Input, Output and Parameter'
                                                      'specifications from the operator definition'
                                                      'in the specified file.')
    generate_parser.set_defaults(command=generate)
    generate_parser.add_argument('-f', '--file',
                                 default=DEFAULT_DEFINITION_FILE,
                                 help='The operator definition file. If not provided, {} is '
                                      'assumed.'.format(DEFAULT_DEFINITION_FILE))

    # Commit
    commit_parser = command_parsers.add_parser('commit',
                                               help='Commit a new version of the operator.',
                                               description='Commit a new version of the operator')
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
    parser = ArgumentParser(prog='operator',
                            description=OPERATOR_COMMAND_HELP)
    add_operator_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
