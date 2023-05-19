from snapstream import Topic


def test_kafka(kafka):
    """Should be able to interact with kafka."""
    t = Topic('test', {
        'bootstrap.servers': kafka,
        'auto.offset.reset': 'earliest',
        'group.id': 'test',
    })

    t('test')

    assert next(t[0]).value() == b'test'
