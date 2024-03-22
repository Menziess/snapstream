from threading import Thread
from time import sleep

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


def test_transaction(cache):
    """Test transaction."""
    result = []

    def try_access_locked_cache():
        result.append(cache['123'])
        cache['123'] = 'b'
        result.append(cache['123'])

    t = Thread(target=try_access_locked_cache)

    with cache.transaction():
        cache['123'] = 'a'

        # Within the transaction, we read and alter cache['123'] and
        # add its value to the result list, mutation shouldn't work
        t.start()
        t.join(timeout=0.01)
        if t.is_alive():
            result.append("Timeout")

        assert result == ['a', 'Timeout']
        assert cache['123'] == 'a'

    # The thread is still running here, so outside of the
    # transaction it will eventually succeed to add 'b'
    sleep(0.01)
    assert cache['123'] == 'b'
