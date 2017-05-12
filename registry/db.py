#!/usr/bin/env python3


from pymongo import MongoClient


REGISTRY_DATABASE = 'mezuri-registry'

client = MongoClient('mongodb://localhost:27017')
db = client[REGISTRY_DATABASE]

class CollectionAccessor:
    def __init__(self, collection):
        self._collection = db[collection]
