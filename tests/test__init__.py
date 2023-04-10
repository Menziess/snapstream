from snapstream import Conf, snap, stream


def test_snap():
    """Should register iterable."""
    Conf().iterables = set()

    iterable = range(1)
    iterable_key = str(id(iterable))
    iterable_item = (iterable_key, iterable)

    @snap(iterable)
    def _(msg):
        return msg

    assert Conf().iterables == set([iterable_item])


def test_stream(mocker):
    """Should start distributing messages for each registered iterable."""
    Conf().iterables = set()
    spy = mocker.spy(Conf(), 'distribute_messages')

    it = range(1)
    iterable_key = str(id(it))
    Conf().register_iterables((iterable_key, it))

    assert spy.call_count == 0
    stream()
    assert spy.call_count == 1
