"""Snapstream public objects."""

import logging
from inspect import signature
from typing import Any, Callable, Generator, Iterable

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

logging.basicConfig()


def _sink_output(s: Callable[..., None], output: Any) -> None:
    if not isinstance(output, tuple) and isinstance(s, (Cache)):
        raise ValueError('Cache sink expects: Tuple[key, val].')
    elif isinstance(output, tuple) and isinstance(s, (Cache, Topic)):
        key, val = output
        s(key=key, val=val)
    else:
        s(output)


def _handle_generator_or_function(
    sink: Iterable[Callable[..., None]],
    output: Any
) -> None:
    if isinstance(output, Generator):
        for val in output:
            for s in sink:
                _sink_output(s, val)
    else:
        for s in sink:
            _sink_output(s, output)


def snap(
    *iterable: Iterable,
    sink: Iterable[Callable[..., None]] = []
):
    """Snaps function to stream.

    Ex:
        >>> topic = Topic('demo')               # doctest: +SKIP
        >>> cache = Cache('state/demo')         # doctest: +SKIP

        >>> @snap(topic, sink=[print, cache])   # doctest: +SKIP
        ... def handler(msg, **kwargs):
        ...     return msg.key(), msg.value()
    """
    c = Conf()

    def _deco(f):
        def _handler(msg, kwargs):
            parameters = signature(f).parameters.values()
            if any(p.kind == p.VAR_KEYWORD for p in parameters):
                output = f(msg, **kwargs)
            elif parameters:
                output = f(msg)
            else:
                output = f()
            _handle_generator_or_function(sink, output)

        for it in iterable:
            iterable_key = str(id(it))
            c.register_iterables((iterable_key, it))
            pub.subscribe(_handler, iterable_key)
        return _handler

    return _deco


def stream(**kwargs):
    """Start the streams.

    Ex:
        >>> args = {
        ...     'env': 'DEV',
        ... }
        >>> stream(**args)
    """
    Conf().start(**kwargs)
