#!/usr/bin/env python3

from argparse import ArgumentParser
from contextlib import contextmanager
import json
import os

from utilities import get_specification, Git, SPECIFICATION_FILE

SPEC_KEY = 'spec'
SPEC_PATH_KEY = 'specPath'

DEFAULT_VERSION = '0.0.0'
operator_context_spec_defaults = {
    'name': None,
    'description': None,
    'version': DEFAULT_VERSION
}


def calculate_operator_context():
    context = {
        SPEC_KEY: operator_context_spec_defaults
    }

    spec, path = get_specification()
    if spec is not None:
        context[SPEC_KEY].update(spec)
        context[SPEC_PATH_KEY] = path

    return context


def save_operator_context(context):
    if SPEC_PATH_KEY in context:
        path = context[SPEC_PATH_KEY]
        del context[SPEC_PATH_KEY]

        with open(path, 'w') as f:
            json.dump(context[SPEC_KEY], f, indent=4)


@contextmanager
def operator_context():
    ctx = calculate_operator_context()
    try:
        yield ctx
    finally:
        save_operator_context(ctx)


def init(_) -> int:
    with operator_context() as ctx:
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
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPECIFICATION_FILE)

    Git.add(SPECIFICATION_FILE)
    return 0


def commit(args):
    with operator_context() as ctx:
        if SPEC_PATH_KEY not in ctx:
            print('Operator not initialized')
            return 1

        # TODO(dibyo): Validate versions
        if args.version is not None:
            ctx[SPEC_KEY]['version'] = args.version

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

