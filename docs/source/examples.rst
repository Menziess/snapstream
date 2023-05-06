.. _examples:

Examples
============

Spin up a local kafka broker using `docker-compose.yml <https://github.com/Menziess/snapstream/blob/master/docker-compose.yml>`_ to follow along:

.. code-block:: bash

  docker compose up broker -d

Can't find what you seek? Create a `new issue <https://github.com/Menziess/snapstream/issues/new>`_.

Topic
-----

Topic can be used to send and receive kafka messages.

- Data is sent to kafka when ``topic`` is called as a function

::

  from snapstream import Topic

  topic = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  }, offset=-2)

  topic('🐟')
  topic(key='key', val='🐟')

  for msg in topic:
      print(msg.key(), msg.value().decode())

- Messages are consumed when ``topic`` is iterated over

::

  None 🐟
  b'key' 🐟

Topic uses `confluent-kafka <https://docs.confluent.io/kafka-clients/python/current/overview.html>`_.

Cache
-----

Cache can be used to persist data.

- Data is cached when ``cache`` is called as a function

::

  from snapstream import Cache

  cache = Cache('db')

  cache('prize', '🏆')

- Data is stored in sst files in the provided folder: ``db``

::

  cache['phone'] = '📞'

  for x, y in cache.items():
      print(x, y)

- Cache is also subscriptable

::

  phone 📞
  prize 🏆

Cache is a basic wrapper around `rocksdict <https://congyuwang.github.io/RocksDict/rocksdict.html>`_.

Conf
----

Conf can be used to set default kafka configurations.

- Conf is a Singleton class, there can only be a single instance

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

  topic2 = Topic('tweets', {'group.id': 'demo'})

  print(topic1.conf)
  print(topic2.conf)

- Default configurations can be overridden per topic

::

  {'bootstrap.servers': 'localhost:29092', 'group.id': 'default-demo'}
  {'bootstrap.servers': 'localhost:29091', 'group.id': 'demo', 'security.protocol': 'SASL_SSL', 'sasl.mechanism': 'PLAIN', 'sasl.username': 'myuser', 'sasl.password': 'mypass'}

Variable return values
----------------------

When your handler function returns zero or more values, use ``yield`` instead of ``return``.

::

  from snapstream import snap, stream

  @snap(range(5), sink=[print])
  def handler(n):
      if n % 2 == 0:
          yield f'equal: {n}'
      if n == 0:
          yield f'zero: {n}'

  stream()

::

  equal: 0
  zero: 0
  equal: 2
  equal: 4

Output stream only
------------------

If there's no incoming data, generators can be used to trigger handler functions.

::

  from time import localtime, sleep, strftime

  from snapstream import snap, stream

  def timer(interval=1.0):
      while True:
          yield
          sleep(interval)

  @snap(timer())
  def handler(msg):
      print(strftime('%H:%M:%S', localtime()))

  stream()

- The ``timer()`` function returns a generator that yields ``None`` every 1.0 seconds

::

  23:25:10
  23:25:11
  23:25:12
  ...

Codec
-----

::

  # TODO
