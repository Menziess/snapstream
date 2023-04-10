from typing import Callable, Iterable

import pytest
from pubsub import pub

from snapstream import Conf
from snapstream.core import ITopic, Topic, get_consumer, get_producer


def test_Conf(mocker):
    """Should distribute messages in parallel."""
    Conf().iterables = set()
    c = Conf({'group.id': 'test'})
    assert c.group_id == 'test'  # type: ignore
    assert c.iterables == set()

    # Register iterable
    iterable = range(1)
    iterable_key = str(id(iterable))
    iterable_item = (iterable_key, iterable)
    c.register_iterables(iterable_item)
    assert c.iterables == set([iterable_item])

    # Subscribe handler
    stub = mocker.stub(name='handler')

    def handler(msg, kwargs):
        stub(msg, kwargs)
    pub.subscribe(handler, iterable_key)

    # Start distributing messages and confirm message was received
    c.start(my_arg='test')
    stub.assert_called_once_with(0, {'my_arg': 'test'})


def test_ITopic():
    """Should not be able to instantiate incorrectly implemented codec."""
    class MyFailingTopic(ITopic):
        pass
    with pytest.raises(TypeError):
        MyFailingTopic()  # type: ignore


def test_get_consumer(mocker):
    """Should ..."""
    with get_consumer('test', {'group.id': 'test'}) as c:
        assert isinstance(c, Iterable)


def test_get_producer():
    """Should ..."""
    with get_producer('test', {}, flush_timeout=0) as p:
        assert isinstance(p, Callable)
        unsent = p('test', 'test')
        assert unsent == 1


def test_Topic():
    """Should ..."""
    assert Topic
