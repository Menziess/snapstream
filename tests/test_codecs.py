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
    """Should ..."""
    assert ICodec


def test_JsonCodec():
    """Should ..."""
    assert JsonCodec


def test_AvroCodec():
    """Should ..."""
    assert AvroCodec
