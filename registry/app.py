#!/usr/bin/env python3

from flask import Flask, abort, make_response, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal
import json

from utilities import temporary_dir, working_dir, SPEC_FILENAME
from utilities.git import Git

registry = Flask(__name__, static_url_path='')
registry_api = Api(registry)


def fetch_remote_spec(remote_url: str, version_hash: str, version_tag: str):
    with temporary_dir() as directory:
        if not Git.clone(remote_url, directory):
            abort(make_response(jsonify({'error': 'Remote repository is not readable'}), 400))

        with working_dir(directory):
            if Git.rev_parse(version_tag) != version_hash:
                abort(make_response(jsonify({'error': 'Remote repository version does not match'}), 400))
            Git.checkout(version_hash)
            with open(SPEC_FILENAME) as f:
                return json.load(f)


def generate_component_api(api: Api, component_type: str,
                           component_endpoint: str, component_list_endpoint: str,
                           version_endpoint: str, version_list_endpoint: str):
    component_for_list_fields = {
        'name': fields.String,
        'uri': fields.Url(endpoint=component_endpoint, absolute=True),
    }
    component_fields = {
        'name': fields.String,
        'uri': fields.Url(endpoint=component_endpoint, absolute=True),
        'gitRemoteUrl': fields.String,
        'versions': fields.List(fields.String),
    }
    components = {}

    class ComponentListAPI(Resource):
        def __init__(self):
            self.parser = reqparse.RequestParser()
            self.parser.add_argument('name', type=str, required=True,
                                     help='Component name not provided',
                                     location='json')
            self.parser.add_argument('gitRemoteUrl', type=str, required=True,
                                     help='Component git remote url not provided',
                                     location='json')
            super().__init__()

        def get(self):
            return {'components': [marshal(component, component_for_list_fields)
                                   for component in components.values()]}

        def post(self):
            args = self.parser.parse_args()

            if args.name in components:
                abort(make_response(jsonify({'error': 'Component already exists'}), 409))

            component = {
                'name': args.name,
                'gitRemoteUrl': args.gitRemoteUrl,
                'versions': []
            }
            components[args.name] = component

            return {'component': marshal(component, component_fields)}, 201

    api.add_resource(ComponentListAPI, '/{}'.format(component_type), endpoint=component_list_endpoint)

    class ComponentAPI(Resource):
        def __init__(self):
            self.parser = reqparse.RequestParser()
            self.parser.add_argument('tag', type=str, required=True,
                                     help='Tag to be published not provided',
                                     location='json')

        def get(self, name: str):
            if name not in components:
                abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

            return {'component': marshal(components[name], component_fields)}

    api.add_resource(ComponentAPI, '/{}/<string:name>'.format(component_type), endpoint=component_endpoint)

    component_version_for_list_fields = {
        'version': fields.String,
        'uri': fields.Url(endpoint=version_endpoint, absolute=True),
        'hash': fields.String
    }
    component_version_fields = {
        'version': fields.String,
        'uri': fields.Url(endpoint=version_endpoint, absolute=True),
        'hash': fields.String,
        'component_name': fields.String,
        'spec': fields.Raw
    }
    component_versions = []

    class ComponentVersionListAPI(Resource):
        def __init__(self):
            self.parser = reqparse.RequestParser()
            self.parser.add_argument('version', type=str, required=True,
                                     help='Version to be published not provided',
                                     location='json')
            self.parser.add_argument('version_tag', type=str, required=True,
                                     help='Version tag not provided',
                                     location='json')
            self.parser.add_argument('version_hash', type=str, required=True,
                                     help='Version hash not provided',
                                     location='json')

        def get(self, component_name):
            if component_name not in components:
                abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

            return {'versions': [marshal(version, component_version_for_list_fields)
                                 for version in component_versions
                                 if version['component_name'] == component_name]}

        def post(self, component_name):
            component = components.get(component_name, None)
            if component is None:
                abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

            args = self.parser.parse_args()
            if args.version in component['versions']:
                abort(make_response(jsonify({'error': 'Component version already exists'}), 409))

            # TODO (dibyo): Fetch spec from git repository for specific version.
            spec = fetch_remote_spec(component['gitRemoteUrl'], args.version_hash, args.version_tag)
            component_version = {
                'version': args.version,
                'hash': args.version_hash,
                'component_name': component_name,
                'spec': spec
            }
            component_versions.append(component_version)
            component['versions'].append(args.version)

            return {'version': marshal(component_version, component_version_fields)}, 201

    api.add_resource(ComponentVersionListAPI,
                     '/{}/<component_name>/versions'.format(component_type),
                     endpoint=version_list_endpoint)

    class ComponentVersionAPI(Resource):
        def get(self, component_name, version):
            if component_name not in components:
                abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

            for component_version in component_versions:
                if component_version['component_name'] == component_name:
                    if component_version['version'] == version:
                        return {
                            'component_version': marshal(component_version, component_version_fields)
                        }

            abort(make_response(jsonify({'error': 'Component version does not exist'}), 404))

    api.add_resource(ComponentVersionAPI,
                     '/{}/<component_name>/versions/<version>'.format(component_type),
                     endpoint=version_endpoint)


generate_component_api(api=registry_api, component_type='operators',
                       component_endpoint='operator', component_list_endpoint='operators',
                       version_endpoint='operator_version', version_list_endpoint='operator_versions')
generate_component_api(api=registry_api, component_type='interfaces',
                       component_endpoint='interface', component_list_endpoint='interfaces',
                       version_endpoint='interface_version', version_list_endpoint='interface_versions')
generate_component_api(api=registry_api, component_type='sources',
                       component_endpoint='source', component_list_endpoint='sources',
                       version_endpoint='source_version', version_list_endpoint='source_versions')


if __name__ == '__main__':
    registry.run(debug=True)
