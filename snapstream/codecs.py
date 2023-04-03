"""Snapstream codecs."""

import logging
from abc import ABCMeta, abstractmethod
from io import BytesIO
from json import dumps, loads
from typing import Any, cast

from avro.io import BinaryDecoder, BinaryEncoder, DatumReader, DatumWriter
from avro.schema import Schema, parse
from toolz import curry

logger = logging.getLogger(__name__)


def deserialize_json(msg: bytes) -> dict:
    """Deserialize json message."""
    return loads(msg.decode('utf-8'))


def serialize_json(msg: dict) -> bytes:
    """Serialize json message."""
    dumped = dumps(msg, default=str)
    return dumped.encode('utf-8')


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


class Codec(metaclass=ABCMeta):
    """Base class for codecs."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name property."""
        ...

    @name.setter
    def name(self, name) -> None:
        self.name = name

    @name.getter
    def name(self) -> str:
        return self.name

    @abstractmethod
    def encode(self, obj: Any) -> bytes:
        """Serialize object."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, s: bytes) -> dict:
        """Deserialize object."""
        raise NotImplementedError


class JsonCodec(Codec):
    """Codec for avro messages."""

    def __init__(self, name: str):
        """Load avro schema."""
        self.name = name

    def encode(self, obj: Any) -> bytes:
        """Serialize message."""
        return serialize_json(obj)

    def decode(self, s: bytes) -> object:
        """Deserialize message."""
        return deserialize_json(s)


class AvroCodec(Codec):
    """Codec for avro messages."""

    def __init__(self, name: str, path: str):
        """Load avro schema."""
        with open(path) as a:
            self.schema = parse(a.read())
        self.name = name

    def encode(self, obj: Any) -> bytes:
        """Serialize message."""
        val = serialize_avro(self.schema, obj)
        return cast(bytes, val)

    def decode(self, s: bytes) -> object:
        """Deserialize message."""
        val = deserialize_avro(self.schema, s)
        return cast(object, val)
