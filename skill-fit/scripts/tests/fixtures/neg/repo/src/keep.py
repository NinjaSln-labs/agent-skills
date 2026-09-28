import os
import sys
import json

CONFIG = {}


def load(name):
    with open(name) as fh:
        return json.load(fh)


def save(name, data):
    pass
