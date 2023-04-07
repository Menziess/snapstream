[![Test Python Package](https://github.com/Menziess/snapstream/actions/workflows/python-test.yml/badge.svg)](https://github.com/Menziess/snapstream/actions/workflows/python-test.yml)

# Snapstream

<img src="https://raw.githubusercontent.com/menziess/snapstream/master/res/logo.png" width="25%" height="25%" align="right" />

A tiny data-flow model with a user-friendly interface that provides sensible defaults for Kafka integration, message serialization/deserialization, and data caching.

## Installation

```sh
pip install snapstream
```

## Usage

We `snap` iterables to user functions, and process them in parallel when we call `stream`:

![demo](res/demo.gif)

We pass the callable `print` to print out the return value. Multiple iterables and sinks can be passed.

```py
from snapstream import snap, stream

@snap(range(5), sink=[print])
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

To try it out for yourself, spin up a local kafka broker with [docker-compose.yml](docker-compose.yml), using `localhost:29091` to connect:

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
