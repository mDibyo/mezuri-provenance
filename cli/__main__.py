#!/usr/bin/env python3

from argparse import ArgumentParser

from .interface import INTERFACE_COMMAND_HELP, add_interface_commands
from .operator import OPERATOR_COMMAND_HELP, add_operator_commands
from .source import SOURCE_COMMAND_HELP, add_source_commands


def main():
    parser = ArgumentParser(prog='mezuri')
    component_parsers = parser.add_subparsers(title='components')

    operator_parser = component_parsers.add_parser('operator',
                                                   help=OPERATOR_COMMAND_HELP,
                                                   description=OPERATOR_COMMAND_HELP)
    operator_parser.set_defaults(component='operator')
    add_operator_commands(operator_parser)

    interface_parser = component_parsers.add_parser('interface',
                                                    help=INTERFACE_COMMAND_HELP,
                                                    description=INTERFACE_COMMAND_HELP)
    interface_parser.set_defaults(component='interface')
    add_interface_commands(interface_parser)

    source_parser = component_parsers.add_parser('source',
                                                 help=SOURCE_COMMAND_HELP,
                                                 description=SOURCE_COMMAND_HELP)
    source_parser.set_defaults(component='source')
    add_source_commands(source_parser)

    args = parser.parse_args()
    if not hasattr(args, 'component'):
        print('No command specified.')
        return 1

    return args.command(args)


main()
