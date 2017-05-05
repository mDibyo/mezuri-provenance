#!/usr/bin/env python3

from argparse import ArgumentParser

from .utils import SPEC_FILENAME, component_init, component_commit, component_publish

OPERATOR_COMMAND_HELP = 'Work with operators.'


def init(_) -> int:
    return component_init()


def commit(args) -> int:
    return component_commit('operator', args.message, args.version)


def publish():
    return component_publish('operator')


def add_operator_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an operator.',
                                             description='Initialize an operator.')
    init_parser.set_defaults(command=init)

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
