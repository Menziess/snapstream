"""Snapstream codecs."""

import logging
from abc import ABCMeta, abstractmethod
from io import BytesIO
from json import dumps, loads
from typing import Any, Union, cast

from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter
from avro.schema import Schema, parse
from toolz import curry

logger = logging.getLogger(__name__)


def deserialize_json(msg: bytes) -> dict:
    """Deserialize json message."""
    return loads(msg.decode())


def serialize_json(msg: dict) -> bytes:
    """Serialize json message."""
    dumped = dumps(msg, default=str)
    return dumped.encode()


@curry
def deserialize_avro(schema: Schema, msg: bytes) -> object:
    """Deserialize avro message using provided schema."""
    try:
        bytes_reader = BytesIO(msg)
        decoder = BinaryDecoder(bytes_reader)
        reader = DatumReader(schema)
        return reader.read(decoder)
    except Exception as e:
        logger.error(f'{e}\nschema:\n{schema}\nmsg:\n{str(msg)}.')
        raise


@curry
def serialize_avro(schema: Schema, msg: dict) -> bytes:
    """Serialize avro message using provided schema."""
    try:
        writer = DatumWriter(schema)
        bytes_writer = BytesIO()
        encoder = BinaryEncoder(bytes_writer)
        writer.write(msg, encoder)
        return bytes_writer.getvalue()
    except Exception as e:
        logger.error(f'{e}\nschema:\n{schema}\nmsg:\n{msg}.')
        raise


class ICodec(metaclass=ABCMeta):
    """Base class for codecs."""

    @abstractmethod
    def encode(self, obj: Any) -> bytes:
        """Serialize object."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, s: bytes) -> object:
        """Deserialize object."""
        raise NotImplementedError


class JsonCodec(ICodec):
    """Serialize/deserialize json messages."""

    def encode(self, obj: Any) -> bytes:
        """Serialize message."""
        return serialize_json(obj)

    def decode(self, s: bytes) -> object:
        """Deserialize message."""
        return deserialize_json(s)


class AvroCodec(ICodec):
    """Serialize/deserialize avro messages."""

    def __init__(self, schema: Union[str, Schema]):
        """Load avro schema."""
        if isinstance(schema, Schema):
            self.schema = schema
        elif isinstance(schema, str):
            with open(schema) as a:
                self.schema = parse(a.read())
        else:
            raise TypeError('Expected .avsc filepath str, or avro.schema.Schema instance.')

    def encode(self, obj: Any) -> bytes:
        """Serialize message."""
        val = serialize_avro(self.schema, obj)
        return cast(bytes, val)

    def decode(self, s: bytes) -> object:
        """Deserialize message."""
        val = deserialize_avro(self.schema, s)
        return cast(object, val)
