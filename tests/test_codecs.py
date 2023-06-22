from avro.schema import parse
import pytest

from snapstream.codecs import (AvroCodec, ICodec, JsonCodec, deserialize_avro,
                               deserialize_json, serialize_avro,
                               serialize_json)


def test_deserialize_json(raw_msg, json_msg):
    """Should deserialize json message."""
    assert deserialize_json(json_msg) == raw_msg


def test_serialize_json(raw_msg, json_msg):
    """Should serialize json message."""
    assert serialize_json(raw_msg) == json_msg


def test_deserialize_avro(raw_msg, avro_msg, avro_schema):
    """Should deserialize avro message."""
    assert deserialize_avro(avro_schema, avro_msg) == raw_msg


def test_serialize_avro(raw_msg, avro_msg, avro_schema):
    """Should serialize avro message."""
    assert serialize_avro(avro_schema, raw_msg) == avro_msg


def test_ICodec():
    """Should not be able to instantiate incorrectly implemented codec."""
    class MyFailingCodec(ICodec):
        pass
    with pytest.raises(TypeError):
        MyFailingCodec()  # type: ignore


def test_JsonCodec(raw_msg, json_msg):
    """Should both serialize and deserialize messages."""
    c = JsonCodec()
    assert c.encode(raw_msg) == json_msg
    assert c.decode(json_msg) == raw_msg


def test_AvroCodec(raw_msg, avro_msg, avro_schema, mocker):
    """Should both serialize and deserialize messages."""
    mock_schema = mocker.mock_open(
        read_data=avro_schema.canonical_form
    )
    mocker.patch('builtins.open', mock_schema)
    c = AvroCodec('schema/myschema.avsc')
    assert c.encode(raw_msg) == avro_msg
    assert c.decode(avro_msg) == raw_msg

    with open('schema/myschema.avsc') as a:
        schema = parse(a.read())

    c = AvroCodec(schema)
    assert c.encode(raw_msg) == avro_msg
    assert c.decode(avro_msg) == raw_msg
