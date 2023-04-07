from snapstream.codecs import deserialize_json, serialize_json


def test_deserialize_json(json_msg, raw_msg):
    """Should deserialize json message."""
    assert deserialize_json(json_msg) == raw_msg


def test_serialize_json(json_msg, raw_msg):
    """Should serialize json message."""
    assert serialize_json(raw_msg) == json_msg
