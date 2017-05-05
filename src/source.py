#!/usr/bin/env python3

from argparse import ArgumentParser

from .utils import component_init, component_commit

SOURCE_COMMAND_HELP = 'Work with sources.'


def init(_):
    return component_init()


def commit(args):
    return component_commit(args.message, args.version)


def add_source_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize a source.',
                                             description='Initialize a source.')
    init_parser.set_defaults(command=init)

    # Commit
    commit_parser = command_parsers.add_parser('commit',
                                               help='Commit a new version of the source.',
                                               description='Commit a new version of the source')
    commit_parser.set_defaults(command=commit)
    commit_parser.add_argument('message',
                               help='The commit message')
    commit_parser.add_argument('-v', '--version',
                               help='The new version of the source. This must be greater '
                                    'than the previous version.')


def main():
    parser = ArgumentParser(prog='source',
                            description=SOURCE_COMMAND_HELP)
    add_source_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
