#!/usr/bin/env python3

from argparse import ArgumentParser
import json
import os

from utilities import (
    SPEC_KEY, SPEC_PATH_KEY, SPEC_FILE, DEFAULT_VERSION,
    Git, Version, component_context
)

operator_context_spec_defaults = {
    'name': None,
    'description': None,
    'version': DEFAULT_VERSION
}


def init(_) -> int:
    with component_context(operator_context_spec_defaults) as ctx:
        if SPEC_PATH_KEY in ctx:
            # TODO(dibyo): Support initializing/re-initializing from passed in
            # JSON-file
            print('Operator already initialized')
            return 1

        spec = ctx[SPEC_KEY]
        spec['name'] = input('Name: ')
        spec['description'] = input('Description: ')
        version = input('Version ({}): '.format(DEFAULT_VERSION))
        spec['version'] = version if version else DEFAULT_VERSION
        print('Please generate input, parameter and output specifications')

        Git.init()
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPEC_FILE)
    Git.add(SPEC_FILE)
    return 0


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


def main():
    parser = ArgumentParser(prog='operator',
                            description='Work with operators.')
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

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
