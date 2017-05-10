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

SOURCE_COMMAND_HELP = 'Work with sources.'

DEFAULT_DEFINITION_FILE = 'source.py'
DEFINITION_CLASS_REF = '__mezuri_source__'


def init(_):
    return component_init()


def generate(args) -> int:
    definition_cls = extract_component_definition(args.file, DEFINITION_CLASS_REF)
    if definition_cls is None:
        print('Could not evaluate operator definition file {}'.format(args.file))

    definition_filename = relpath(args.file, get_project_root_by_specification())
    io_specs = definition_cls._AbstractSource__extract_spec()
    with component_context() as ctx:
        ctx[SPEC_KEY]['iop_declaration'] = OrderedDict((method, OrderedDict((
            ('uri', io_specs[method]['uri']),
            ('query', io_specs[method]['query']),
            ('output', OrderedDict((name, type_.serialize())
                                   for name, type_ in io_specs[method]['output']))
        ))) for method in sorted(io_specs.keys()))
        ctx[SPEC_KEY]['definition'] = definition_filename

    Git.add(SPEC_FILENAME)
    Git.add(definition_filename)
    return 0


def commit(args):
    return component_commit('source', args.message, Version(args.version) if args.version else None)


def publish():
    return component_publish('source')


def add_source_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize a source.',
                                             description='Initialize a source.')
    init_parser.set_defaults(command=init)

    # Generate
    generate_parser = command_parsers.add_parser('generate',
                                                 help='Generate the Output and Source'
                                                      'specifications from the source definition'
                                                      'in the specified file.')
    generate_parser.set_defaults(command=generate)
    generate_parser.add_argument('-f', '--file',
                                 default=DEFAULT_DEFINITION_FILE,
                                 help='The source definition file. If not provided, {} is '
                                      'assumed.'.format(DEFAULT_DEFINITION_FILE))

    # Commit
    commit_parser = command_parsers.add_parser('commit',
                                               help='Commit a new version of the source.',
                                               description='Commit a new version of the source')
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
    parser = ArgumentParser(prog='source',
                            description=SOURCE_COMMAND_HELP)
    add_source_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
