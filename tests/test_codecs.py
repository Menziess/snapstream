from snapstream.codecs import (AvroCodec, ICodec, JsonCodec, deserialize_avro,
                               deserialize_json, serialize_avro,
                               serialize_json)


def test_deserialize_json(json_msg, raw_msg):
    """Should deserialize json message."""
    assert deserialize_json(json_msg) == raw_msg


def test_serialize_json(json_msg, raw_msg):
    """Should serialize json message."""
    assert serialize_json(raw_msg) == json_msg


def test_deserialize_avro(raw_msg):
    """Should ..."""
    assert deserialize_avro


def test_serialize_avro(raw_msg):
    """Should ..."""
    assert serialize_avro


def test_ICodec():
    """Should ..."""
    assert ICodec


def test_JsonCodec():
    """Should ..."""
    assert JsonCodec


def test_AvroCodec():
    """Should ..."""
    assert AvroCodec
