#!/usr/bin/env python3


from argparse import ArgumentParser

from .utilities import component_init, component_commit

INTERFACE_COMMAND_HELP = 'Work with interfaces.'


def init(_):
    return component_init()


def commit(args):
    return component_commit(args.message, args.version)


def add_interface_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an interface.',
                                             description='Initialize an interface.')
    init_parser.set_defaults(command=init)

    # Commit
    # Commit
    commit_parser = command_parsers.add_parser('commit',
                                               help='Commit a new version of the interface.',
                                               description='Commit a new version of the interface')
    commit_parser.set_defaults(command=commit)
    commit_parser.add_argument('message',
                               help='The commit message')
    commit_parser.add_argument('-v', '--version',
                               help='The new version of the interface. This must be greater '
                                    'than the previous version.')


def main():
    parser = ArgumentParser(prog='interface',
                            description=INTERFACE_COMMAND_HELP)
    add_interface_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
