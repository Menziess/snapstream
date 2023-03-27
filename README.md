# Snapstream

**Note:** this project is work in progress.

## Usage

The `Conf()` singleton object contains default configurations:

```py
from snapstream import Conf, Topic, snap, stream

Conf({'group.id': '$Default', 'bootstrap.servers': 'localhost:29091'})

cache = Cache('state/db')  # stores data in rocksdb

t = Topic('flights', {
    'sasl.username': 'AUEOZPERNVZW2',
    'sasl.password': '*******',
})
```

The topic and the cache can be passed to the `snap` decorator:

```py
@snap(topic, sink=[cache])
def cache_flight(msg):
    """Process incoming flight and cache in rocksdb."""
    val = msg.value()
    key = val['flight_id']

    flight = {
        'id': val['flight_id'],
        'origin': val['inbound_flight_location'],
        'destination': val['outbound_flight_location'],
    }
    return key, flight
```

The `cache_flight` function will handle any incoming messages, and store them in the cache.

We can set up a mock events stream by creating a generator function:

```py
def mock_events():
    for i in range(10):
        yield i, f'MockEvent'


@snap(mock_events(), sink=[print])
def join_streams(msg):
    """Use id to find flight in cache."""
    id, event = msg
    flight = cache[id]
    result = {
        **flight,
        'event': event,
    }
    return id, result


if __name__ == "__main__":
    stream()
```

The `join_streams` function handles incoming mock messages, and uses the id to find the associated flight from the cache.

When all streams are "snapped" to the handler functions, we call `stream()` to start all data streams.
