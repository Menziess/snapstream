from snapstream import Conf, snap, stream


def test_snap():
    """Should register iterable."""
    Conf().iterables = set()

    @snap(range(1))
    def _(msg):
        return msg

    _, it = list(Conf().iterables).pop()
    assert it == range(1)


def test_stream():
    """Should start processing an unsnapped iterable."""
    Conf().iterables = set()
    it = range(1)
    iterable_key = str(id(it))
    Conf().register_iterables((iterable_key, it))
    assert stream() is None
