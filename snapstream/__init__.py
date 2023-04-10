"""Snapstream public objects."""

from typing import Iterable

from pubsub import pub

from snapstream.caching import Cache
from snapstream.core import READ_FROM_END, READ_FROM_START, Conf, Topic

__all__ = [
    'snap',
    'stream',
    'Conf',
    'Topic',
    'Cache',
    'READ_FROM_START',
    'READ_FROM_END',
]


def snap(
    *iterable: Iterable,
    sink: Iterable = []
):
    """Snaps function to stream.

    Ex:
        >> topic = Topic('demo')
        >> cache = Cache('state/demo')

        >> @snap(topic, sink=[print, cache])
        .. def handler(msg, **kwargs):
        ..     return msg.key(), msg.value()
    """
    c = Conf()

    def sink_output(s, output):
        if not isinstance(output, tuple) and isinstance(s, (Cache)):
            # Sink requires Tuple[key, val]
            raise ValueError('Cache sink expects: Tuple[key, val].')
        elif isinstance(output, tuple) and isinstance(s, (Cache, Topic)):
            key, val = output
            s(key=key, val=val)
        else:
            s(output)

    def _deco(f):
        def _handler(msg, kwargs):
            try:
                output = f(msg, **kwargs)
            except TypeError:
                output = f(msg)
            for s in sink:
                sink_output(s, output)

        for it in iterable:
            iterable_key = str(id(it))
            c.register_iterables((iterable_key, it))
            pub.subscribe(_handler, iterable_key)
        return _handler

    return _deco


def stream(**kwargs):
    """Start the streams.

    Ex:
        >> args = {
        ..     'env': 'DEV',
        .. }
        >> stream(**args)
    """
    Conf().start(**kwargs)
