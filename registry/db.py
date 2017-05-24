#!/usr/bin/env python3


from pymongo import MongoClient


REGISTRY_DATABASE = 'mezuri-registry'

client = MongoClient('mongodb', 27017)
db = client[REGISTRY_DATABASE]
