
from snapstream.utils import KafkaIgnoredPropertyFilter, Singleton


def test_Singleton():
    """Should maintain a single instance of a class."""
    class MySingleton(metaclass=Singleton):
        def __update__(self):
            pass

    a = MySingleton()
    b = MySingleton()

    assert a is b


def test_KafkaIgnoredPropertyFilter():
    """Should ..."""
    assert KafkaIgnoredPropertyFilter
