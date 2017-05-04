#!/usr/bin/env python3

import contextlib
import json

from .utilities import get_specification

SPEC_PATH_KEY = 'specPath'

operator_context_defaults = {
    'name': None,
    'description': None,
    'version': '0.0.0'
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
    path = context[SPEC_PATH_KEY]
    del context[SPEC_PATH_KEY]

    with open(path, 'w') as f:
        json.dump(f, context)


@contextlib.contextmanager
def operator_context():
    ctx = calculate_operator_context()
    try:
        yield ctx
    finally:
        save_operator_context(ctx)


def init():
    with operator_context() as ctx:
        pass


def commit():
    pass


def publish():
    pass
