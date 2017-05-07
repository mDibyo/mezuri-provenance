#!/usr/bin/env python3

from flask import Flask, abort, make_response, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal

app = Flask(__name__, static_url_path='/publish')
api = Api(app)


operator_fields = {
    'name': fields.String,
    'uri': fields.Url(endpoint='operator', absolute=True),
    'gitRemoteUrl': fields.Url,
    'tag': fields.String
}

operators = {}


@app.errorhandler(404)
def not_found(_):
    return make_response(jsonify({'error': 'Component not found'}), 404)


@app.errorhandler(409)
def conflict(_):
    return make_response(jsonify({'error': 'Component already exists'}), 409)


class OperatorListAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True,
                                 help='Operator name not provided',
                                 location='json')
        self.parser.add_argument('gitRemoteUrl', type=str, required=True,
                                 help='Operator git remote url not provided',
                                 location='json')
        self.parser.add_argument('tag', type=str, required=True,
                                 help='Tag to be published not provided',
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
            'tag': args.tag
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

    def put(self, name: str):
        abort(501)

    def delete(self, name: str):
        abort(501)


api.add_resource(OperatorListAPI, '/operators', endpoint='operators')
api.add_resource(OperatorAPI, '/operators/<string:name>', endpoint='operator')


if __name__ == '__main__':
    app.run(debug=True)
