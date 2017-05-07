#!/usr/bin/env python3

from flask import Flask, abort, make_response, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal

registry = Flask(__name__, static_url_path='')
registry_api = Api(registry)


@registry.errorhandler(404)
def not_found(_):
    return make_response(jsonify({'error': 'Component not found'}), 404)


@registry.errorhandler(409)
def conflict(_):
    return make_response(jsonify({'error': 'Component already exists'}), 409)


operator_fields = {
    'name': fields.String,
    'uri': fields.Url(endpoint='operator', absolute=True),
    'gitRemoteUrl': fields.Url,
    'versions': fields.List(fields.String),
}
operators = {}


class OperatorListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True,
                                 help='Operator name not provided',
                                 location='json')
        self.parser.add_argument('gitRemoteUrl', type=str, required=True,
                                 help='Operator git remote url not provided',
                                 location='json')
        super().__init__()

    def get(self):
        return {'operators': [marshal(operator, operator_fields)
                              for operator in operators.values()]}

    def post(self):
        args = self.parser.parse_args()

        if args.name in operators:
            abort(409)

        operator = {
            'name': args.name,
            'gitRemoteUrl': args.gitRemoteUrl,
            'versions': []
        }
        operators[args.name] = operator

        return {'operator': marshal(operator, operator_fields)}, 201


class OperatorAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag', type=str, required=True,
                                 help='Tag to be published not provided',
                                 location='json')

    def get(self, name: str):
        if name not in operators:
            abort(404)

        return {'operator': marshal(operators[name], operator_fields)}


registry_api.add_resource(OperatorListAPI, '/operators', endpoint='operators')
registry_api.add_resource(OperatorAPI, '/operators/<string:name>', endpoint='operator')


operator_version_fields = {
    'version': fields.String,
    'uri': fields.Url(endpoint='operator_version', absolute=True),
    'operator_name': fields.String,
    'spec': fields.Raw
}
operator_versions = []


class OperatorVersionListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('version', type=str, required=True,
                                 help='Tag to be published not provided',
                                 location='json')

    def get(self, operator_name):
        return {'versions': [version for version in operator_versions
                             if version['operator_name'] == operator_name]}

    def post(self, operator_name):
        operator = operators.get(operator_name, None)
        if operator is None:
            abort(404)

        args = self.parser.parse_args()
        if args.version in operator['versions']:
            abort(409)

        # TODO (dibyo): Fetch spec from git repository
        operator_versions.append({
            'version': args.version,
            'operator_name': operator_name,
            'spec': None
        })
        operator['versions'].append(args.version)


class OperatorVersionAPI(Resource):
    def get(self, operator_name, version):
        for operator_version in operator_versions:
            if operator_version['operator_name'] == operator_name:
                if operator_version['version'] == version:
                    return {
                        'operator_version': marshal(operator_version, operator_version_fields)
                    }

        abort(404)


registry_api.add_resource(OperatorVersionListAPI, '/operators/<operator_name>/versions',
                          endpoint='operator_versions')
registry_api.add_resource(OperatorVersionAPI, '/operators/<operator_name>/versions/<version>',
                          endpoint='operator_version')


if __name__ == '__main__':
    registry.run(debug=True)
