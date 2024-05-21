"""Kafka is not isolated, bear in mind when writing tests."""

import logging

import pytest
from toolz import last

from snapstream import Topic
from snapstream.core import READ_FROM_START


def test_produce_no_kafka(caplog):
    """Should fail to produce to missing broker."""
    t = Topic('test', {
        'bootstrap.servers': 'localhost:1000',
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test',
        'group.id': 'test',
    }, flush_timeout=0.01)

    t('test')
    t('test')  # second call triggers poll() for first message
    _, lvl, log = caplog.record_tuples[0]

    assert lvl == logging.ERROR
    assert log.startswith('FAIL [rdkafka#producer-')
    assert 'Connection refused' in log

    del t  # trigger flush (with 0.01s timeout)


def test_consume_no_kafka(caplog, timeout):
    """Should fail to consume from missing broker."""
    t = Topic('test', {
        'bootstrap.servers': 'localhost:1000',
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test',
        'group.id': 'test',
    })

    with pytest.raises(TimeoutError):
        with timeout(1):
            next(t)

    _, lvl, log = caplog.record_tuples[0]
    assert lvl == logging.ERROR
    assert log.startswith('FAIL [rdkafka#consumer-')
    assert 'Connection refused' in log


def test_produce_consume(kafka):
    """Should be able to exchange messages with kafka."""
    t = Topic('test_produce_consume', {
        'bootstrap.servers': kafka,
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test_produce_consume',
        'group.id': 'test_produce_consume',
    })

    t('test')

    assert next(t[0]).value() == b'test'

    # Close consumer before KafkaContainer goes down
    del t


def test_slice_dice(kafka):
    """Should be able to exchange messages with kafka."""
    t = Topic('test_slice_dice', {
        'bootstrap.servers': kafka,
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test_slice_dice',
        'group.id': 'test_slice_dice',
    }, offset=READ_FROM_START)

    for x in range(3):
        t(f'test{x}')

    # Consume Last in slice, should close consumer
    assert last(t[:2]).value() == b'test2'

    # Consume first
    assert next(t[0]).value() == b'test0'

    # Continue after first
    for i, msg in enumerate(t):
        assert msg.value() == f'test{i + 1}'.encode()
        if i == 1:
            break

    # Close consumer before KafkaContainer goes down
    del t
