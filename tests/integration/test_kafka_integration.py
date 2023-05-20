"""Kafka is not isolated, bear in mind when writing tests."""

import logging

import pytest

from snapstream import Topic


def test_produce_no_kafka(caplog):
    """Should fail to produce to missing broker."""
    t = Topic('test', {
        'bootstrap.servers': 'localhost:1000',
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test',
        'group.id': 'test',
    }, flush_timeout=0.01)

    t('test')
    del t  # trigger flush (with 0.01s timeout)

    _, lvl, log = caplog.record_tuples[0]
    assert lvl == logging.ERROR
    assert log.startswith('FAIL [rdkafka#producer-')
    assert 'Connection refused' in log


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
    t = Topic('test', {
        'bootstrap.servers': kafka,
        'auto.offset.reset': 'earliest',
        'group.instance.id': 'test',
        'group.id': 'test',
    })

    t('test')

    assert next(t[0]).value() == b'test'
