# Snapstream

<img src="https://raw.githubusercontent.com/menziess/snapstream/master/res/logo.png" width="25%" height="25%" align="right" />

A tiny data-flow model with a user-friendly interface that provides sensible defaults for Kafka integration, message serialization/deserialization, and data caching.

## Installation

```sh
pip install snapstream
```

## Usage

We `snap` the iterable `range(5)` to the handler function:

```py
from snapstream import snap, stream

r = range(5)

@snap(r, sink=[print])
def handler(msg):
    return f'Hello {msg}'

stream()
```

```sh
Hello 0
Hello 1
Hello 2
Hello 3
Hello 4
```

Here's a more interesting example using `Topic` to transmit and `Cache` to persist data:

```py
from snapstream import Cache, Topic, snap, stream
from time import sleep

messages = ('🐌', '🚬', '😁', '🐢', '👑')

# RocksDB is a persistent key-value store
cache = Cache('db/demo')

# Each topic may have its own configuration
topic = Topic('demo', conf={
    'group.id': 'demo',
    'group.instance.id': 'demo',
    'bootstrap.servers': 'localhost:29091',
})


@snap(messages, sink=[topic])
def send_to_topic(msg):
    # topic acts as a callable
    return msg


@snap(topic, sink=[cache])
def add_key_and_cache(msg):
    # and here it acts as an iterable
    val = msg.value().decode()
    key = ord(val)
    return key, val


def inspect_cache():
    keys = (ord(_) for _ in messages)
    for key in keys:
        while not (value := cache[key]):
            sleep(0.1)
        yield value


@snap(inspect_cache(), sink=[print])
def read_from_cache(msg):
    return f'Look at this emoji: {msg}'


stream()
```

```sh
Look at this emoji: 🐌
Look at this emoji: 🚬
Look at this emoji: 😁
Look at this emoji: 🐢
Look at this emoji: 👑
```

Spin up a local kafka broker using [docker-compose.yml](docker-compose.yml), and try it out for yourself:

```sh
docker compose up broker -d
```

## Features

- [`snapstream.snap`](snapstream/__init__.py): bind streams (iterables) and sinks (callables) to user defined handler functions
- [`snapstream.stream`](snapstream/__init__.py): start streaming
- [`snapstream.Topic`](snapstream/core.py): consume from (iterable) and produce to (callable) kafka using [**confluent-kafka**](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html)
- [`snapstream.Cache`](snapstream/caching.py): store data to disk using [**rocksdict**](https://congyuwang.github.io/RocksDict/rocksdict.html)
- [`snapstream.Conf`](snapstream/core.py): set global kafka configuration (can be overridden per topic)
- [`snapstream.codecs.AvroCodec`](snapstream/codecs.py): serialize and deserialize avro messages
- [`snapstream.codecs.JsonCodec`](snapstream/codecs.py): serialize and deserialize json messages
