
import logging

import pytest

from snapstream.utils import KafkaIgnoredPropertyFilter, Singleton


def test_Singleton():
    """Should maintain a single instance of a class."""
    class MySingleton(metaclass=Singleton):
        def __update__(self):
            pass

    a = MySingleton()
    b = MySingleton()

    assert a is b


@pytest.mark.parametrize('lvl,msg,shown', [
    (logging.WARNING, 'property and will be ignored', False),
    (logging.WARNING, 'other message', True),
    (logging.INFO, 'property and will be ignored', True),
])
def test_KafkaIgnoredPropertyFilter(lvl, msg, shown):
    """Should ignore certain types of warnings."""
    f = KafkaIgnoredPropertyFilter()

    r = logging.LogRecord(
        '',
        lvl,
        pathname='',
        lineno=0,
        msg=msg,
        args=None,
        exc_info=None
    )

    assert f.filter(r) is shown
