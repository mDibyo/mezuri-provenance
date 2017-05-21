#!/usr/bin/env python3

from abc import abstractmethod
from collections import OrderedDict
from flask import Flask, abort, make_response, jsonify
from flask_restful import Api, Resource, reqparse, fields, marshal
import json

from registry.db import db
from common import temporary_dir, working_dir, SPEC_FILENAME, ComponentInfo
from common.git import Git

REGISTRY_URL_PATH = 'http://127.0.0.1:5000'

registry = Flask(__name__, static_url_path='')
registry_api = Api(registry)


def fetch_remote_specs(remote_url: str, version_hash: str, version_tag: str):
    with temporary_dir() as directory:
        if not Git.clone(remote_url, directory):
            abort(make_response(jsonify({'error': 'Remote repository is not readable'}), 400))

        with working_dir(directory):
            if Git.rev_parse(version_tag) != version_hash:
                abort(make_response(jsonify({'error': 'Remote repository version does not match'}), 400))
            Git.checkout(version_hash)
            with open(SPEC_FILENAME) as f:
                return json.load(f, object_pairs_hook=OrderedDict)


class ComponentVersionUtils(object):
    @property
    @abstractmethod
    def component_type(self):
        return NotImplemented

    @property
    @abstractmethod
    def version_endpoint(self):
        return NotImplemented

    @property
    @abstractmethod
    def component_collection(self):
        return NotImplemented

    @property
    @abstractmethod
    def version_collection(self):
        return NotImplemented

    dependents_collection = db['component_dependents']

    @property
    def component_version_fields(self):
        return {
            'version': fields.String,
            'uri': fields.Url(endpoint=self.version_endpoint, absolute=True),
            'hash': fields.String,
            'componentName': fields.String(attribute='component_name'),
            'specs': fields.Raw
        }

    @property
    def component_version_for_list_fields(self):
        return {
            'version': fields.String,
            'uri': fields.Url(endpoint=self.version_endpoint, absolute=True),
            'hash': fields.String
        }

    @property
    def component_version_dependents_fields(self):
        return {
            'componentType': fields.String(attribute='component_type'),
            'registryUrl': fields.String(attribute='registry_url'),
            'componentName': fields.String(attribute='component_name'),
            'componentVersion': fields.String(attribute='component_version'),
        }


class AbstractComponentVersionAPI(Resource, ComponentVersionUtils):
    def get(self, component_name, version):
        if self.component_collection.find_one({'name': component_name}) is None:
            abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

        component_version = self.version_collection.find_one({
            'component_name': component_name,
            'version': version
        })

        if component_version is not None:
            return {'componentVersion': marshal(component_version, self.component_version_fields)}

        abort(make_response(jsonify({'error': 'Component version does not exist'}), 404))


class AbstractComponentVersionListAPI(Resource, ComponentVersionUtils):
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
        if self.component_collection.find_one({'name': component_name}) is None:
            abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

        return {'versions': [marshal(version, self.component_version_for_list_fields)
                             for version in self.version_collection.find({'component_name': component_name})]}

    def post(self, component_name):
        component = self.component_collection.find_one({'name': component_name})
        if component is None:
            abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

        args = self.parser.parse_args()
        if args.version in component['versions']:
            abort(make_response(jsonify({'error': 'Component version already exists'}), 409))

        # Fetch specifications from remote repository
        specs = fetch_remote_specs(component['gitRemoteUrl'], args.version_hash, args.version_tag)
        component_version = {
            'version': args.version,
            'hash': args.version_hash,
            'component_name': component_name,
            'specs': specs
        }
        self.version_collection.insert_one(component_version)
        component['versions'].append(args.version)
        self.component_collection.replace_one({'_id': component['_id']}, component)

        # Update dependents
        component_version_dependent_info = ComponentInfo(self.component_type, REGISTRY_URL_PATH,
                                                         component_name, args.version)
        try:
            for component_info in map(lambda info: ComponentInfo(
                info['componentType'],
                info['registryUrl'],
                info['componentName'],
                info['componentVersion']
            ), specs['dependencies']):
                dependents_info = self.dependents_collection.find_one({
                    'dependency': component_info._asdict()
                })
                if dependents_info is not None:
                    dependents_info['dependents'].append(component_version_dependent_info._asdict())
                    self.dependents_collection.replace_one({'_id': dependents_info['_id']},
                                                           dependents_info)
                else:
                    dependents_info = {
                        'dependency': component_info._asdict(),
                        'dependents': [component_version_dependent_info._asdict()]
                    }
                    print(dependents_info)
                    self.dependents_collection.insert_one(dependents_info)
        except ValueError:
            pass

        return {'componentVersion': marshal(component_version, self.component_version_fields)}, 201


class AbstractComponentVersionDependentsAPI(Resource, ComponentVersionUtils):
    def get(self, component_name, version):
        component_version_dependent_info = ComponentInfo(self.component_type, REGISTRY_URL_PATH,
                                                         component_name, version)
        print(component_version_dependent_info._asdict())
        dependents = self.dependents_collection.find_one({
            'dependency.component_version': component_version_dependent_info.component_version,
            'dependency.component_name': component_version_dependent_info.component_name
        })
        return {'dependentsInfo': marshal(dependents['dependents'] if dependents is not None else [],
                                          self.component_version_dependents_fields)}, 200


def generate_component_api(api: Api, component_type: str,
                           component_endpoint: str, component_list_endpoint: str):
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
    component_collection = db[component_list_endpoint]

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
                                   for component in component_collection.find()]}

        def post(self):
            args = self.parser.parse_args()

            if component_collection.find_one({'name': args.name}) is not None:
                abort(make_response(jsonify({'error': 'Component already exists'}), 409))

            component = {
                'name': args.name,
                'gitRemoteUrl': args.gitRemoteUrl,
                'versions': []
            }
            component_collection.insert_one(component)

            return {'component': marshal(component, component_fields)}, 201

    api.add_resource(ComponentListAPI, '/{}'.format(component_type), endpoint=component_list_endpoint)

    class ComponentAPI(Resource):
        def __init__(self):
            self.parser = reqparse.RequestParser()
            self.parser.add_argument('tag', type=str, required=True,
                                     help='Tag to be published not provided',
                                     location='json')

        def get(self, name: str):
            component = component_collection.find_one({'name': name})
            if component is None:
                abort(make_response(jsonify({'error': 'Component does not exist'}), 404))

            return {'component': marshal(component, component_fields)}

    api.add_resource(ComponentAPI, '/{}/<string:name>'.format(component_type), endpoint=component_endpoint)


class OperatorVersionUtils(ComponentVersionUtils):
    component_type = 'operators'

    version_endpoint = 'operator_version'

    component_collection = db['operators']
    version_collection = db['operator_versions']


class OperatorVersionListApi(OperatorVersionUtils, AbstractComponentVersionListAPI):
    pass

registry_api.add_resource(OperatorVersionListApi,
                          '/operators/<component_name>/versions',
                          endpoint='operator_versions')


class OperatorVersionAPI(OperatorVersionUtils, AbstractComponentVersionAPI):
    pass

registry_api.add_resource(OperatorVersionAPI,
                          '/operators/<component_name>/versions/<version>',
                          endpoint='operator_version')


class OperatorVersionDependentsAPI(OperatorVersionUtils, AbstractComponentVersionDependentsAPI):
    pass

registry_api.add_resource(OperatorVersionDependentsAPI,
                          '/operators/<component_name>/versions/<version>/dependents',
                          endpoint='operator_version_dependents')


class SourceVersionUtils(ComponentVersionUtils):
    component_type = 'sources'

    version_endpoint = 'source_version'

    component_collection = db['sources']
    version_collection = db['source_versions']


class SourceVersionListAPI(SourceVersionUtils, AbstractComponentVersionListAPI):
    pass

registry_api.add_resource(SourceVersionListAPI,
                          '/sources/<component_name>/versions',
                          endpoint='source_versions')


class SourceVersionAPI(SourceVersionUtils, AbstractComponentVersionAPI):
    pass

registry_api.add_resource(SourceVersionAPI,
                          '/sources/<component_name>/versions/<version>',
                          endpoint='source_version')


class SourceVersionDependentsAPI(SourceVersionUtils, AbstractComponentVersionDependentsAPI):
    pass

registry_api.add_resource(SourceVersionDependentsAPI,
                          '/sources/<component_name>/versions/<version>/dependents',
                          endpoint='source_version_dependents')


class InterfaceVersionUtils(ComponentVersionUtils):
    component_type = 'interfaces'

    version_endpoint = 'interface_version'

    component_collection = db['interfaces']
    version_collection = db['interface_versions']


class InterfaceVersionListApi(InterfaceVersionUtils, AbstractComponentVersionListAPI):
    pass

registry_api.add_resource(InterfaceVersionListApi,
                          '/interfaces/<component_name>/versions',
                          endpoint='interface_versions')


class InterfaceVersionAPI(InterfaceVersionUtils, AbstractComponentVersionAPI):
    pass

registry_api.add_resource(InterfaceVersionAPI,
                          '/interfaces/<component_name>/versions/<version>',
                          endpoint='interface_version')


class InterfaceVersionDependentsAPI(InterfaceVersionUtils, AbstractComponentVersionDependentsAPI):
    pass

registry_api.add_resource(InterfaceVersionDependentsAPI,
                          '/interfaces/<component_name>/versions/<version>/dependents',
                          endpoint='interface_version_dependents')


generate_component_api(api=registry_api, component_type='operators',
                       component_endpoint='operator', component_list_endpoint='operators')
generate_component_api(api=registry_api, component_type='interfaces',
                       component_endpoint='interface', component_list_endpoint='interfaces')
generate_component_api(api=registry_api, component_type='sources',
                       component_endpoint='source', component_list_endpoint='sources')


@registry.after_request
def apply_caching(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    registry.run(debug=True)
