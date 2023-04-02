# Snapstream

<img src="https://github.com/Menziess/snapstream/blob/feature/github-actions/res/logo.png?raw=true" width="25%" height="25%" align="right" />

A tiny data-flow model with a user-friendly interface that provides sensible defaults for Kafka integration, message serialization/deserialization, and data caching.

In response to a challenge of performing a "merge-as-of", "nearby join", or "merge by key distance" operation on multiple kafka streams while reading topics from separate kafka clusters, this package was born.

No actual stream or external database is required, cached data is persisted to disk using rocksdb, applications using snapstream are more inclined to be; self-contained, easy to extend, less complex, easy to test using regular iterables:

## Installation

```sh
pip install snapstream
```

## Usage

In the example below, `snap` decorates the `handle` function, binding the iterable `range(5)` to it:

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

## Features

- `snapstream.Topic`: an iterable/callable to consume and produce (default: [**confluent-kafka**](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html))
- `snapstream.Cache`: a callable/dict to persist data (default: [**rocksdict**](https://congyuwang.github.io/RocksDict/rocksdict.html))
- `snapstream.Conf`: a singleton object, can be used to store common kafka configurations
- `snapstream.snap`: a function to bind streams (iterables) and sinks (callables) to user defined handler functions
- `snapstream.stream`: a function to start the streams
