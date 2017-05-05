#!/usr/bin/env python3

from flask import Flask
from flask.ext.restful import Api, Resource

app = Flask(__name__, static_url_path='/publish')
api = Api(app)


operators = []


class OperatorListAPI(Resource):
    def get(self):
        return {'operators': operators}

    def post(self):
        pass


class OperatorAPI(Resource):
    def get(self, name: str):
        pass

    def put(self, name: str):
        pass

    def delete(self, name: str):
        pass


api.add_resource(OperatorListAPI, '/operators', endpoint='operators')
api.add_resource(OperatorAPI, '/operators/<str:name>', endpoint='operator')
