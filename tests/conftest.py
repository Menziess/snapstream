"""Common testing functionalities."""

from json import dumps

from avro.schema import Schema, parse
from pytest import fixture

from snapstream import Cache

_avro_schema = parse(dumps({
    'type': 'record',
    'name': 'testing',
    'namespace': 'snapstream',
    'fields': [
        {'name': 'null', 'type': 'null'},
        {'name': 'boolean', 'type': 'boolean'},
        {'name': 'int', 'type': 'int'},
        {'name': 'string', 'type': 'string'},
    ]
}))


_msg: dict = {
    'null': None,
    'boolean': True,
    'int': 33,
    'string': 'test',
}
_json_msg = b'{"null": null, "boolean": true, "int": 33, "string": "test"}'
_avro_msg = b'\x01B\x08test'


@fixture
def raw_msg() -> dict:
    """Get unserialized message."""
    return _msg


@fixture
def json_msg() -> bytes:
    """Get serialized json message."""
    return _json_msg


@fixture
def avro_msg() -> bytes:
    """Get serialized avro message."""
    return _avro_msg


@fixture
def avro_schema() -> Schema:
    """Get avro schema."""
    return _avro_schema


@fixture
def cache() -> Cache:
    """Get Cache instance."""
    return Cache('tests/db')
