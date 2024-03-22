.. _examples:

Examples
============

Each example is self-contained. Can't find what you seek? Create a `new issue <https://github.com/Menziess/snapstream/issues/new>`_.

Topic
-----

Topic can be used to send and receive kafka messages.

- Data is sent to kafka when ``topic`` is called as a function
- Messages can be consumed by iterating over the ``topic`` object

::

  from snapstream import Topic

  topic = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'auto.offset.reset': 'earliest',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  }, offset=-2)

  topic('🐟')
  topic(key='key', val='🐟')

  for msg in topic:
      print(msg.key(), msg.value().decode())


::

  None 🐟
  b'key' 🐟

Topic uses `confluent-kafka <https://docs.confluent.io/kafka-clients/python/current/overview.html>`_.

Cache
-----

Cache can be used to persist data.

- Data is cached when ``cache`` is called as a function
- Data is stored in sst files in the specified folder: ``db``

::

  from snapstream import Cache

  cache = Cache('db')

  cache('prize', '🏆')
  cache['phone'] = '📞'

  for x, y in cache.items():
      print(x, y)

::

  phone 📞
  prize 🏆

To avoid race conditions, lock database keys using the ``transaction`` context manager:

::

  with cache.transaction('fish'):
      cache['fish'] = '🐟'

Cache is a basic wrapper around `rocksdict <https://congyuwang.github.io/RocksDict/rocksdict.html>`_.

Conf
----

Conf can be used to set default kafka configurations.

- Conf is a Singleton class, only one instance exists
- Configurations can be overridden per topic

::

  from snapstream import Conf, Topic

  Conf({
      'bootstrap.servers': 'localhost:29091',
      'group.id': 'default-demo',
  })

  topic1 = Topic('emoji', {'bootstrap.servers': 'localhost:29092'})

  Conf({
      'security.protocol': 'SASL_SSL',
      'sasl.mechanism': 'PLAIN',
      'sasl.username': 'myuser',
      'sasl.password': 'mypass',
  })

  topic2 = Topic('conf', {'group.id': 'demo'})

  print(topic1.conf)
  print(topic2.conf)

::

  {'bootstrap.servers': 'localhost:29092', 'group.id': 'default-demo'}
  {'bootstrap.servers': 'localhost:29091', 'group.id': 'demo', 'security.protocol': 'SASL_SSL', 'sasl.mechanism': 'PLAIN', 'sasl.username': 'myuser', 'sasl.password': 'mypass'}

Yield
-----

When your handler function returns zero or more values, use ``yield`` instead of ``return``.

::

  from snapstream import snap, stream

  @snap(range(5), sink=[print])
  def handler(n):
      if n % 2 == 0:
          yield f'even: {n}'
      if n == 0:
          yield f'zero: {n}'

  stream()

::

  even: 0
  zero: 0
  even: 2
  even: 4

Timer
-----

If there's no incoming data, generators can be used to trigger handler functions.

- The ``timer()`` function returns a generator that yields ``None`` every 1.0 seconds

::

  from time import localtime, sleep, strftime

  from snapstream import snap, stream

  def timer(interval=1.0):
      while True:
          yield
          sleep(interval)

  @snap(timer())
  def handler():
      print(strftime('%H:%M:%S', localtime()))

  stream()

::

  23:25:10
  23:25:11
  23:25:12
  ...

Codec
-----

Codecs are used for serializing and deserializing data.

- Using ``JsonCodec`` values are automatically converted to and from json

::

  from snapstream import Topic
  from snapstream.codecs import JsonCodec, ICodec

  topic = Topic('codecs', {
      'bootstrap.servers': 'localhost:29091',
      'auto.offset.reset': 'earliest',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  }, offset=-2, codec=JsonCodec())

  topic({'msg': '🐟'})

  for msg in topic:
      print(msg.value())

::

  {'msg': '🐟'}

- It's possible to create custom codecs by extending ``ICodec``

::

  class AvroCodec(ICodec):
    """Serializes/deserializes avro messages."""

    def __init__(self, path: str):
        """Load avro schema."""
        with open(path) as a:
            self.schema = parse(a.read())

    def encode(self, obj: Any) -> bytes:
        """Serialize message."""
        val = serialize_avro(self.schema, obj)
        return cast(bytes, val)

    def decode(self, s: bytes) -> object:
        """Deserialize message."""
        val = deserialize_avro(self.schema, s)
        return cast(object, val)

Slicing
-------

To read a specific range or single offset from kafka, use the slice notation:

::

  from snapstream import Topic

  topic = Topic('slicing', {
      'bootstrap.servers': 'localhost:29091',
      'auto.offset.reset': 'earliest',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  })

  for x in '🏆', '📞', '🐟', '👌':
      topic(x)

  for x in topic[3]:
      print(x.value().decode(), x.offset())

It's recommended to never use ``list`` or any active operation that collects all data, as the stream may be unbounded.
Here's the message at offset 3:

::

  👌 3

If we want to get offsets 0 up until 3, we can slice the topic:

::

  for x in topic[0:3]:
      print(x.value().decode(), x.offset())

::

  🏆 0
  📞 1
  🐟 2

If the retention period could have surpassed that of the first message, it's worth using ``-2`` as the first offset.
In the following snippet, we also pass a step of ``2``, taking every second message:

::

  for x in topic[-2::2]:
      print(x.value().decode(), x.offset())

::

  🏆 0
  🐟 2
  ...

You'll also notice that the program keeps waiting until the stop condition has been met.
