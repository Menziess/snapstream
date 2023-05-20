"""Common testing functionalities."""

import signal
from contextlib import contextmanager
from json import dumps
from typing import Iterator

from avro.schema import Schema, parse
from pytest import fixture
from testcontainers.kafka import KafkaContainer

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
def cache() -> Iterator[Cache]:
    """Get Cache instance that automatically cleans itself."""
    c = Cache('tests/db')
    try:
        yield c
    finally:
        c.close()
        c.destroy()


@fixture(scope='session')
def kafka():
    """Get running kafka broker."""
    kafka = KafkaContainer()
    kafka.start()
    yield kafka.get_bootstrap_server()
    kafka.stop()


@fixture
def timeout():
    """Contextmanager that will stop execution of body."""
    @contextmanager
    def set_timeout(seconds: int):
        def raise_timeout(*_):
            raise TimeoutError(f'Timeout reached: {seconds}.')

        def start_timeout():
            signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(seconds)
        yield start_timeout()
    return set_timeout
