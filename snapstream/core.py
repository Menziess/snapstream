"""Snapstream core objects."""

import logging
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from queue import Queue
from re import sub
from threading import Thread, current_thread
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Set,
    Tuple,
    cast,
)

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from pubsub import pub
from toolz import pipe

from snapstream.codecs import ICodec
from snapstream.utils import KafkaIgnoredPropertyFilter, Singleton

logger = logging.getLogger(__name__)
logger.addFilter(KafkaIgnoredPropertyFilter())

READ_FROM_START = -2
READ_FROM_END = -1


class Conf(metaclass=Singleton):
    """Define default kafka configuration, optionally.

    >>> Conf({'bootstrap.servers': 'localhost:29091'})
    {'bootstrap.servers': 'localhost:29091'}
    """

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
        except BaseException as e:
            logger.debug(f'Exception in thread {current_thread().name}.')
            queue.put(e)
        finally:
            queue.put(None)
            logger.debug(f'Stopping thread {current_thread().name}.')

    def start(self, **kwargs):
        """Start the streams."""
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
            exit()
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

        - Should allow `*args`, `**kwargs` passthrough to kafka client.
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


def _consumer_handler(c, poll_timeout, codec, raise_error, commit_each_message):
    while True:
        msg = c.poll(poll_timeout)
        if msg is None:
            continue
        if err := msg.error():
            if raise_error or err.fatal() or not err.retriable():
                raise KafkaException(err)
            else:
                logger.error(msg.error())
                continue
        if codec:
            decoded_val = codec.decode(msg.value())
            msg.set_value(decoded_val)

        yield msg

        if commit_each_message:
            c.commit()


def _producer_handler(p, topic, poll_timeout, codec, dry):
    def callback(err, msg):
        if err is not None:
            logger.error(f'Failed to deliver message: {err}.')
            # Raise exception by default
            raise KafkaException(err)
        else:
            logger.debug(f'Produced to topic: {msg.topic()}.')

    def produce(key, val, *args, **kwargs):
        if codec:
            logger.debug(f'Encoding using codec: {topic}.')
            val = codec.encode(val)
        if dry:
            logger.warning(f'Skipped sending message to {topic} [dry=True].')
            return
        p.produce(topic=topic, key=key, value=val, *args, **kwargs, callback=callback)
        p.poll(poll_timeout)
    return produce


class Topic(ITopic):
    """Act as a consumer and producer.

    >>> topic = Topic('emoji', {
    ...     'bootstrap.servers': 'localhost:29091',
    ...     'auto.offset.reset': 'earliest',
    ...     'group.id': 'demo',
    ... })

    Loop over topic (iterable) to consume from it:

    >>> for msg in topic:               # doctest: +SKIP
    ...     print(msg.value())

    Call topic (callable) with data to produce to it:

    >>> topic({'msg': 'Hello World!'})  # doctest: +SKIP
    """

    def __init__(
        self,
        name: str,
        conf: dict = {},
        offset: Optional[int] = None,
        codec: Optional[ICodec] = None,
        flush_timeout: float = -1.0,
        poll_timeout: float = 1.0,
        pusher=_producer_handler,
        poller=_consumer_handler,
        dry: bool = False,
        raise_error: bool = False,
        commit_each_message: bool = False
    ) -> None:
        """Pass topic related configuration."""
        c = Conf()
        self.name = name
        self.conf = {**c.conf, **conf}
        self.starting_offset = offset
        self.flush_timeout = flush_timeout
        self.poll_timeout = poll_timeout
        self._consumer = None
        self._producer = None
        self._producer_callable = None
        self._producer_ctx_mgr = None
        self.pusher = pusher
        self.poller = poller
        self.codec = codec
        self.dry = dry
        self.raise_error = raise_error
        self.commit_each_message = commit_each_message

    def admin(self):
        """Get admin client."""
        return AdminClient(self.conf)

    def create_topic(self, *args, **kwargs) -> None:
        """Create topic."""
        admin = AdminClient(self.conf)
        for t, f in admin.create_topics([NewTopic(self.name, *args, **kwargs)]).items():
            try:
                f.result()
                logger.debug(f"Topic {t} created.")
            except KafkaException as e:
                if "TOPIC_ALREADY_EXISTS" in str(e):
                    logger.warning(e)
                else:
                    logger.error(e)
                    raise

    @contextmanager
    def _get_consumer(self) -> Iterator[Iterable[Any]]:
        """Yield an iterable to consume from kafka."""
        self._consumer = Consumer(self.conf, logger=logger)
        commit_each_message = pipe(
            self.conf.get('enable.auto.commit'),
            str,
            str.lower
        ) == 'false' and self.commit_each_message

        def consume():
            def on_assign(c, ps):
                for p in ps:
                    if self.starting_offset is not None:
                        p.offset = self.starting_offset
                c.assign(ps)

            logger.debug(f'Subscribing to topic: {self.name}.')
            cast(Consumer, self._consumer).subscribe([self.name], on_assign=on_assign)
            logger.debug(f'Consuming from topic: {self.name}.')
            yield from self.poller(self._consumer, self.poll_timeout, self.codec,
                                   self.raise_error, commit_each_message)
        yield consume()
        leave_msg = (
            'Leaving group'
            if commit_each_message
            else 'Committing offsets and leaving group'
        )
        logger.debug(f'{leave_msg}, flush_timeout={self.flush_timeout}.')
        self._consumer.close()

    @contextmanager
    def _get_producer(self) -> Iterator[Callable[[Any, Any], None]]:
        """Yield kafka produce method."""
        self._producer = self._producer or Producer(self.conf, logger=logger)
        yield self.pusher(self._producer, self.name, self.poll_timeout, self.codec, self.dry)
        logger.debug(f'Flushing messages to kafka, flush_timeout={self.flush_timeout}.')
        self._producer.flush(self.flush_timeout)

    def __iter__(self) -> Iterator[Any]:
        """Consume from topic."""
        c = self._get_consumer()
        with c as consumer:
            for msg in consumer:
                yield msg

    def __next__(self) -> Any:
        """Consume next message from topic."""
        c = self._get_consumer()
        with c as consumer:
            for msg in consumer:
                return msg

    def __getitem__(self, i) -> Any:
        """Consume specific range of messages from topic."""
        if not isinstance(i, (slice, int)):
            raise TypeError('Expected slice or int.')
        start, step, stop = (
            i,
            None,
            i + 1 if i >= 0 else None
        ) if isinstance(i, int) else (
            i.start,
            i.step,
            i.stop
        )
        c = self._get_consumer()
        with c as consumer:
            for msg in consumer:
                if start and start > msg.offset():
                    continue
                if stop and msg.offset() >= stop:
                    return
                if step and (msg.offset() - max(0, start)) % step != 0:
                    continue
                yield msg

    def __call__(self, val, key=None, *args, **kwargs) -> None:
        """Produce to topic."""
        if not self._producer_callable:
            self._producer_ctx_mgr = self._get_producer()
            self._producer_callable = self._producer_ctx_mgr.__enter__()
        self._producer_callable(key, val, *args, **kwargs)

    def __del__(self):
        """Cleanup and finalization."""
        if self._producer_ctx_mgr:
            self._producer_ctx_mgr.__exit__(None, None, None)
