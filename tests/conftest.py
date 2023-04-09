"""Common testing functionalities."""

from json import dumps

from pytest import fixture

from snapstream import Cache

avro_schema = str({
    'type': 'record',
    'name': 'testing',
    'namespace': 'snapstream',
    'fields': [
        {'name': 'string', 'type': 'string'}
    ]
})


msg: dict = {
    'string': 'test',
}


@fixture
def raw_msg() -> dict:
    """Get unserialized message."""
    return msg


@fixture
def json_msg() -> bytes:
    """Get serialized json message."""
    return dumps(msg).encode()


@fixture
def cache() -> Cache:
    """Get Cache instance."""
    return Cache('tests/db')
