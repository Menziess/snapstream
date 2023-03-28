"""Snapstream core objects."""

import logging
from contextlib import contextmanager
from re import sub
from typing import Any, Callable, Dict, Iterable, Iterator, Optional

from confluent_kafka import Consumer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from pubsub import pub

from snapstream.codecs import Codec
from snapstream.utils import Singleton

logger = logging.getLogger(__file__)


class Conf(metaclass=Singleton):
    """Defines app configuration."""

    iterables = set()

    def start(self):
        """Start the streams."""
        # TODO: run topic iterables in separate threads (>1)
        # TODO: run iterables async
        for it in self.iterables:
            iterable_key = str(id(it))
            for el in it:
                pub.sendMessage(iterable_key, msg=el)

    def register_iterables(self, *it):
        """Add iterables to global Conf."""
        self.iterables.add(*it)

    def __init__(self, conf: dict = {}, state_dir: Optional[str] = None) -> None:
        """Define init behavior."""
        self.conf: Dict[str, Any] = {}
        self.state_dir = state_dir
        self.__update__(conf)

    def __update__(self, conf: dict = {}):
        """Set default app configuration."""
        self.conf = {**self.conf, **conf}
        for key, value in conf.items():
            key = sub('[^0-9a-zA-Z]+', '_', key)
            setattr(self, key, value)

    def __repr__(self) -> str:
        """Represent config."""
        return str(self.conf)


@contextmanager
def get_consumer(
    topic: str,
    conf: dict,
    offset=None,
    codec: Optional[Codec] = None
) -> Iterator[Iterator[Any]]:
    """Yield an iterable to consume from kafka."""
    c = Consumer(conf, logger=logger)

    def consume():
        def on_assign(c, ps):
            for p in ps:
                if offset:
                    p.offset = offset
            c.assign(ps)

        logger.debug(f'Subscribing to topic: {topic}.')
        c.subscribe([topic], on_assign=on_assign)

        logger.debug(f'Consuming from topic: {topic}.')
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if err := msg.error():
                raise KafkaException(err)
            if codec:
                decoded_val = codec.decode(msg.value())
                msg.set_value(decoded_val)
            yield msg
    try:
        yield consume()
    finally:
        c.close()


class Topic:
    """Act as producer and consumer."""

    def __init__(
        self,
        name: str,
        *args,
        conf: dict = {},
        is_leader=False,
        offset: Optional[int] = None,
        codec: Optional[Codec] = None,
        **kwargs,
    ) -> None:
        """Pass topic related configuration."""
        c = Conf()
        self.name = name
        self.conf = {**c.conf, **conf}
        self.is_leader = is_leader
        self.starting_offset = offset
        self.codec = codec

    def create_topic(self, name: str, *args, **kwargs):
        """Create topic if it doesn't exist and is_leader=True."""
        if not self.is_leader:
            return
        admin = AdminClient(self.conf)
        for t, f in admin.create_topics([NewTopic(name, *args, **kwargs)]).items():
            try:
                f.result()
                logger.info(f"Topic {t} created.")
            except KafkaException as e:
                if "TOPIC_ALREADY_EXISTS" in str(e):
                    logger.warning(e)
                else:
                    logger.error(e)
                    raise

    def __iter__(self):
        """Consume from topic."""
        c = get_consumer(self.name, self.conf, self.starting_offset, self.codec)
        with c as consumer:
            for msg in consumer:
                yield msg

    def __call__(self, *args, **kwargs):
        """Produce to topic."""
        print("Produced:", *args, **kwargs)

    def __del__(self):
        """Remove self from global Conf."""
        Conf().iterables.remove(self)


def snap(
    *iterable: Iterable,
    sink: Iterable[Callable[[Any], None]],
    cache: Optional[str] = None,
):
    """Snaps function to stream."""
    c = Conf()
    if cache and not c.state_dir:
        raise RuntimeError("Specify state_dir in Conf() first.")

    # TODO: setup rocksdb cache
    def _deco(f):
        def _handler(msg):
            processed_msg = f(msg)
            for s in sink:
                # TODO: cache message
                s(processed_msg)

        for it in iterable:
            c.register_iterables(it)
            iterable_key = str(id(it))
            pub.subscribe(_handler, iterable_key)
        return _handler

    return _deco


def stream():
    """Start the streams."""
    Conf().start()
