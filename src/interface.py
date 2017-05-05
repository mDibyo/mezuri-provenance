#!/usr/bin/env python3


from argparse import ArgumentParser
import os

from utilities import (
    SPEC_KEY, SPEC_PATH_KEY, SPEC_FILE, DEFAULT_VERSION,
    component_context, Git
)


def init(_):
    with component_context() as ctx:
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

        Git.init()
        ctx[SPEC_PATH_KEY] = os.path.join(os.getcwd(), SPEC_FILE)
    Git.add(SPEC_FILE)
    return 0


def main():
    parser = ArgumentParser(prog='interface',
                            description='Work with interfaces.')
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an operator.',
                                             description='Initialize an operator.')
    init_parser.set_defaults(command=init)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
