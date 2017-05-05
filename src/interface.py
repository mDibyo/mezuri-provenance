#!/usr/bin/env python3


from argparse import ArgumentParser

from .utilities import component_init

INTERFACE_COMMAND_HELP = 'Work with interfaces.'


def init(_):
    return component_init()


def add_interface_commands(parser):
    command_parsers = parser.add_subparsers(title='commands')

    # Init
    init_parser = command_parsers.add_parser('init',
                                             help='Initialize an operator.',
                                             description='Initialize an operator.')
    init_parser.set_defaults(command=init)


def main():
    parser = ArgumentParser(prog='interface',
                            description=INTERFACE_COMMAND_HELP)
    add_interface_commands(parser)

    args = parser.parse_args()
    return args.command(args)


if __name__ == '__main__':
    main()
