# Snapstream

<img src="res/logo.png" width="25%" height="25%" align="right" />

An easy to use, extensible data-flow model, providing sensible defaults to produce and consume to and from kafka, serialize/deserialize messages, and cache large amounts of data.

## Installation

```sh
pip install snapstream
```

## Usage

In the example below, `snap` decorates the `handle` function, binding the iterable `range(5)` to it:

```py
from snapstream import snap, stream


@snap(range(5))
def handle(msg):
    print('Greetings', msg)

stream()
```

```sh
➜ python main.py
Greetings 0
Greetings 1
Greetings 2
Greetings 3
Greetings 4
```

## Features

- `snapstream.Topic`: consume from topic (iterable), produce to topic (callable), uses [**confluent-kafka**](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html) by default
- `snapstream.Cache`: persist data, uses [**rocksdict**](https://congyuwang.github.io/RocksDict/rocksdict.html)
- `snapstream.Conf`: configuration singleton class, manages threads for all streams
- `snapstream.stream`: start streams
- `snapstream.snap`: bind streams (iterable) and sinks (callable) to handler functions
