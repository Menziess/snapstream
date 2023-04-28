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


def test_kwargable_function():
    """Should try to pass kwargs to user defined handler function."""
    my_kwargs = {
        'my_kwarg': 'kwarg value'
    }
    is_kwargable = False
    is_unkwargable = False

    @snap(range(1))
    def kwargable(msg, **kwargs):
        nonlocal is_kwargable
        is_kwargable = kwargs == my_kwargs

    @snap(range(1))
    def unkwargable(msg):
        nonlocal is_unkwargable
        is_unkwargable = msg == 0

    stream(**my_kwargs)

    assert is_kwargable is True
    assert is_unkwargable is True
