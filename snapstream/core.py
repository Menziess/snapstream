"""Snapstream core objects."""

import logging
from contextlib import contextmanager
from queue import Queue
from re import sub
from threading import Event, Thread
from typing import Any, Callable, Dict, Iterator, Optional

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from pubsub import pub

from snapstream.codecs import Codec
from snapstream.utils import KafkaIgnoredPropertyFilter, Singleton

logger = logging.getLogger(__file__)

READ_FROM_START = -2
READ_FROM_END = -1


class Conf(metaclass=Singleton):
    """Defines app configuration."""

    iterables = set()

    def start(self, **kwargs):
        """Start the streams."""
        logger.addFilter(KafkaIgnoredPropertyFilter())

        def spread_iterable_messages(it, queue, stop_signal):
            iterable_key = str(id(it))
            try:
                for el in it:
                    if stop_signal.is_set():
                        break
                    pub.sendMessage(iterable_key, msg=el, kwargs=kwargs)
            except Exception as e:
                queue.put(e)
                stop_signal.set()

        queue, stop_signal = Queue(maxsize=1), Event()
        threads = [
            Thread(
                target=spread_iterable_messages,
                args=(it, queue, stop_signal)
            )
            for it in self.iterables
        ]

        for t in threads:
            t.start()

        raise queue.get()

    def register_iterables(self, *it):
        """Add iterables to global Conf."""
        self.iterables.add(*it)

    def __init__(self, conf: dict = {}) -> None:
        """Define init behavior."""
        self.conf: Dict[str, Any] = {}
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


@contextmanager
def get_producer(
    topic: str,
    conf: dict,
    dry=False,
    codec: Optional[Codec] = None
) -> Iterator[Callable[[Any, Any], Any]]:
    """Yield kafka produce method."""
    p = Producer(conf, logger=logger)

    def _acked(err, msg):
        if err is not None:
            logger.error(f'Failed to deliver message: {err}.')
            # Bubble up every single error
            raise KafkaException(err)
        else:
            logger.debug(f'Produced to topic: {topic}.')

    def produce(key, val, *args, **kwargs):
        if codec:
            logger.debug(f'Encoding using codec: {topic}.')
            val = codec.encode(val)
        if dry:
            logger.warning(f'Skipped sending message to {topic} [dry=True].')
            return
        p.produce(topic=topic, key=key, value=val, *args, **kwargs, callback=_acked)
        # Immediately send every message
        p.flush()

    yield produce

    p.flush()


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
        self.producer = None
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

    def __call__(self, val, key=None, * args, dry=False, **kwargs):
        """Produce to topic."""
        self.producer = (
            self.producer or
            get_producer(self.name, self.conf, dry, self.codec).__enter__()
        )
        self.producer(key, val, *args, **kwargs)
