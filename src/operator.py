#!/usr/bin/env python3

from argparse import ArgumentParser
import json

from .utilities import (
    SPEC_KEY, SPEC_PATH_KEY, SPEC_FILE, DEFAULT_VERSION,
    Git, Version, component_context, component_init
)

OPERATOR_COMMAND_HELP = 'Work with operators.'

operator_context_spec_defaults = {
    'name': None,
    'description': None,
    'version': DEFAULT_VERSION
}


def init(_) -> int:
    return component_init(operator_context_spec_defaults)


def commit(args):
    with component_context(operator_context_spec_defaults) as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Operator not initialized')
            return 1

        if args.version is not None:
            ctx[SPEC_KEY]['version'] = args.version
        current_version = Version(ctx[SPEC_KEY]['version'])
        last_spec_raw = Git.show('HEAD', SPEC_FILE)
        if last_spec_raw is not None:
            last_spec = json.loads(last_spec_raw)
            last_version = Version(last_spec['version'])
            if last_version >= current_version:
                print('Version {} not greater than {}'.format(current_version, last_version))
                return 1

    Git.commit(args.message)
    return 0


def publish():
    pass


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
                                    'than the previous version.')


def main():
    parser = ArgumentParser(prog='operator',
                            description=OPERATOR_COMMAND_HELP)
    add_operator_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
