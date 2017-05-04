#!/usr/bin/env python3

from argparse import ArgumentParser
from contextlib import contextmanager
import json
import os

from utilities import get_specification, Git, SPECIFICATION_FILE

SPEC_PATH_KEY = 'specPath'

DEFAULT_VERSION = '0.0.0'
operator_context_defaults = {
    'name': None,
    'description': None,
    'version': DEFAULT_VERSION
}


def calculate_operator_context():
    context = {}
    context.update(operator_context_defaults)
    spec, path = get_specification()
    if spec is not None:
        context.update(spec)
        context[SPEC_PATH_KEY] = path

    return context


def save_operator_context(context):
    if SPEC_PATH_KEY in context:
        path = context[SPEC_PATH_KEY]
        del context[SPEC_PATH_KEY]

        with open(path, 'w') as f:
            json.dump(context, f, indent=4)


@contextmanager
def operator_context():
    ctx = calculate_operator_context()
    try:
        yield ctx
    finally:
        save_operator_context(ctx)


def init() -> int:
    with operator_context() as ctx:
        if SPEC_PATH_KEY in ctx:
            print('Operator already initialized')
            return 1

        ctx['name'] = input('Name: ')
        ctx['description'] = input('Description: ')
        ctx['version'] = input('Version ({}): '.format(DEFAULT_VERSION))

        Git.init()
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPECIFICATION_FILE)
        return 0


def commit():
    pass


def publish():
    pass


if __name__ == '__main__':
    parser = ArgumentParser(prog='operator')
    parser.add_argument('command', help='The command to be executed. ')
    args = parser.parse_args()

    if args.command == 'init':
        exit(init())
