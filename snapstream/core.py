"""Snapstream core objects."""

import logging
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from queue import Queue
from re import sub
from threading import Thread, current_thread
from typing import (Any, Callable, Dict, Iterable, Iterator, Optional, Set,
                    Tuple)

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from pubsub import pub

from snapstream.codecs import ICodec
from snapstream.utils import KafkaIgnoredPropertyFilter, Singleton

logger = logging.getLogger(__file__)

READ_FROM_START = -2
READ_FROM_END = -1


class Conf(metaclass=Singleton):
    """Defines app configuration."""

    iterables: Set[Tuple[str, Iterable]] = set()

    def register_iterables(self, *it):
        """Add iterables to global Conf."""
        self.iterables.add(*it)

    @staticmethod
    def distribute_messages(it, queue, kwargs):
        """Publish messages from iterable."""
        iterable_key = str(id(it))
        try:
            for el in it:
                pub.sendMessage(iterable_key, msg=el, kwargs=kwargs)
        except Exception as e:
            logger.debug(f'Exception in thread {current_thread().name}.')
            queue.put(e)
        finally:
            queue.put(None)
            logger.debug(f'Stopping thread {current_thread().name}.')

    def start(self, **kwargs):
        """Start the streams."""
        logger.addFilter(KafkaIgnoredPropertyFilter())

        queue = Queue(maxsize=1)
        threads = [
            Thread(
                target=self.distribute_messages,
                args=(it, queue, kwargs)
            )
            for _, it in self.iterables
        ]

        try:
            for t in threads:
                logger.debug(f'Spawning thread {t.name}.')
                t.daemon = True
                t.start()
            while any(t.is_alive() for t in threads):
                if exception := queue.get():
                    raise exception
        except KeyboardInterrupt:
            logger.info('You stopped the program.')
        finally:
            self.iterables = set()

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


class ITopic(metaclass=ABCMeta):
    """Base class for topic implementations."""

    @abstractmethod
    def __init__(
        self,
        name: str,
        conf: Dict[str, Any] = {},
        offset: Optional[int] = None,
        codec: Optional[ICodec] = None,
        **kwargs: Dict[str, Any]
    ) -> None:
        """Initialize topic instance.

        - Should use Conf().conf as default kafka configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def create_topic(self, name: str, *args: Any, **kwargs: Dict[str, Any]) -> None:
        """Create topic.

        - Should allow *args, **kwargs passthrough to kafka client.
        - Should log warning if topic already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def __iter__(self) -> Iterable[Any]:
        """Consume from topic.

        - Should instantiate consumer when called (iterated over).
        - Should deserialize using topic codec.
        - Should use topic offset attribute.
        """
        raise NotImplementedError

    @abstractmethod
    def __call__(self, val, key=None, * args, dry: bool = False, **kwargs: Dict[str, Any]) -> None:
        """Produce to topic.

        - Should instantiate producer when first called (function call).
        - Should set producer on topic producer attribute.
        - Should use topic producer attribute in susequent calls.
        - Should serialize using topic codec.
        - Should skip sending message when dry is True.
        - Should show a warning when skipped.
        """
        raise NotImplementedError


@contextmanager
def get_consumer(
    topic: str,
    conf: dict,
    offset=None,
    codec: Optional[ICodec] = None,
    poll_timeout: float = 1.0
) -> Iterator[Iterable[Any]]:
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
            msg = c.poll(poll_timeout)
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
    codec: Optional[ICodec] = None,
    flush_timeout: float = -1.0
) -> Iterator[Callable[[Any, Any], int]]:
    """Yield kafka produce method."""
    p = Producer(conf, logger=logger)

    def _acked(err, msg):
        if err is not None:
            logger.error(f'Failed to deliver message: {err}.')
            # Bubble up every single error
            raise KafkaException(err)
        else:
            logger.debug(f'Produced to topic: {topic}.')

    def produce(key, val, *args, **kwargs) -> int:
        if codec:
            logger.debug(f'Encoding using codec: {topic}.')
            val = codec.encode(val)
        if dry:
            logger.warning(f'Skipped sending message to {topic} [dry=True].')
            return 0
        p.produce(topic=topic, key=key, value=val, *args, **kwargs, callback=_acked)
        # Immediately send every message
        return p.flush(flush_timeout)

    yield produce

    p.flush(flush_timeout)


class Topic(ITopic):
    """Act as producer and consumer."""

    def __init__(
        self,
        name: str,
        conf: dict = {},
        offset: Optional[int] = None,
        codec: Optional[ICodec] = None,
        flush_timeout: float = -1.0,
        poll_timeout: float = 1.0,
        **kwargs,
    ) -> None:
        """Pass topic related configuration."""
        c = Conf()
        self.name = name
        self.conf = {**c.conf, **conf}
        self.starting_offset = offset
        self.flush_timeout = flush_timeout
        self.poll_timeout = poll_timeout
        self.producer = None
        self.codec = codec

    def create_topic(self, name: str, *args, **kwargs) -> None:
        """Create topic."""
        admin = AdminClient(self.conf)
        for t, f in admin.create_topics([NewTopic(name, *args, **kwargs)]).items():
            try:
                f.result()
                logger.debug(f"Topic {t} created.")
            except KafkaException as e:
                if "TOPIC_ALREADY_EXISTS" in str(e):
                    logger.warning(e)
                else:
                    logger.error(e)
                    raise

    def __iter__(self) -> Iterator[Any]:
        """Consume from topic."""
        c = get_consumer(self.name, self.conf, self.starting_offset,
                         self.codec, self.poll_timeout)
        with c as consumer:
            for msg in consumer:
                yield msg

    def __call__(self, val, key=None, *args, dry=False, **kwargs) -> None:
        """Produce to topic."""
        self.producer = (
            self.producer or
            get_producer(self.name, self.conf, dry, self.codec, self.flush_timeout).__enter__()
        )
        self.producer(key, val, *args, **kwargs)
