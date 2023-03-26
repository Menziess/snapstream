"""Snapstream core objects."""

import logging
from re import sub
from time import sleep
from typing import Any, Dict, Generator, Iterable, Optional

# from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from pubsub import pub

from snapstream.codecs import Codec
from snapstream.utils import Singleton

logger = logging.getLogger(__file__)


class Conf(metaclass=Singleton):
    """Defines app configuration."""

    topics = set()

    def start(self):
        """Start the streams."""
        for t in self.topics:
            list(t)

    def register_topics(self, *topic):
        """Add topics to global Conf."""
        self.topics.add(*topic)

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
        c.register_topics(self)

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
        while True:
            msg = "some msg"
            print("Consumed:", msg)
            pub.sendMessage(str(id(self)), msg=msg)
            sleep(1)

    def __call__(self, *args, **kwargs):
        """Produce to topic."""
        print("Produced:", *args, **kwargs)

    def __del__(self):
        """Remove self from global Conf."""
        Conf().topics.remove(self)


def snap(
    *topics: Generator,
    sink: Iterable[Topic],
    cache: Optional[str] = None,
):
    """Snaps function to stream."""
    c = Conf()
    if cache and not c.state_dir:
        raise RuntimeError("Specify state_dir in Conf() first.")

    # TODO: setup rocksdb cache
    def _deco(f):
        def _handler(msg):
            k, v = f(msg)
            for s in sink:
                # TODO: cache message
                s(k, v)

        for t in topics:
            pub.subscribe(_handler, str(id(t)))
        return _handler

    return _deco


def stream():
    """Start the streams."""
    Conf().start()
