from typing import Callable, Iterable

import pytest
from confluent_kafka.admin import NewTopic
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
    """Should not be able to instantiate incorrectly implemented Topic."""
    class MyFailingTopic(ITopic):
        pass
    with pytest.raises(TypeError):
        MyFailingTopic()  # type: ignore


def test_get_consumer():
    """Should return an interable."""
    with get_consumer('test', {'group.id': 'test'}, poll_timeout=0) as c:
        assert isinstance(c, Iterable)


def test_get_producer(mocker):
    """Should return a callable."""
    with get_producer('test', {}, flush_timeout=0) as p:
        assert isinstance(p, Callable)
        p('test', 'test')


def test_Topic(mocker):
    """Should use provided poller and callback to interact with Kafka."""
    key, val = 123, 'message'
    admin = mocker.stub(name='admin')
    mocker.patch('confluent_kafka.admin.AdminClient.create_topics', admin)
    poller = mocker.MagicMock(return_value=[
        mocker.Mock(
            key=lambda: key,
            value=lambda: val
        )
    ])
    produce = mocker.stub(name='produce')
    pusher = mocker.MagicMock(return_value=produce)

    t = Topic('test', {
        'group.id': 'test'
    }, poller=poller, pusher=pusher)

    # Should try and create topic
    t.create_topic()
    admin.assert_called_once_with([NewTopic(topic='test')])

    # Should try and consume messages
    for msg in t:
        assert msg.key() == key
        assert msg.value() == val
    poller.assert_called_once()

    # Should try and produce messages
    t(val, key)
    produce.assert_called_once_with(key, val)
