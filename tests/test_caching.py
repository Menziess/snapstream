import pytest


@pytest.mark.serial
@pytest.mark.parametrize('key,val,updated', [
    (b'123', 'a', 'b'),
    ('123', 'b', 'c'),
    (True, 'c', 'd'),
    (123, 'd', 'e'),
])
def test_crud(key, val, updated, cache):
    """Test create/read/update/delete."""
    cache[key] = val
    assert cache[key] == val
    cache[key] = updated
    assert cache[key] == updated
    del cache[key]
    assert cache[key] is None


def test_iterability(cache):
    """Test iterability."""
    cache[123] = 123
    it = cache.iter()
    it.seek_to_first()

    assert it.valid()
    while it.valid():
        assert it.key() == 123
        assert it.value() == 123
        it.next()

    assert list(cache.keys()) == [123]
    assert list(cache.values()) == [123]
    assert list(cache.items()) == [(123, 123)]
