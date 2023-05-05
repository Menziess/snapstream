.. _examples:

Examples
============

Can't find what you seek? Create a `new issue <https://github.com/Menziess/snapstream/issues/new>`_.

Spin up a local kafka broker using `docker-compose.yml <https://github.com/Menziess/snapstream/blob/master/docker-compose.yml>`_ to follow along:

.. code-block:: bash

  docker compose up broker -d

Topic
-----

To produce and consume data from kafka, create a Topic instance.

- A message is sent to kafka by calling ``topic`` as a function

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

- Messages are consumed when iterated over ``topic``

::

  None 🐟
  b'key' 🐟

Topic uses `confluent-kafka <https://docs.confluent.io/kafka-clients/python/current/overview.html>`_.

Cache
-------

To cache data, create a Cache instance.

- A Cache instance is also callable, but always requires a key

::

  # TODO

Conf
----

Conf can be used to set default kafka configurations.

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

::

  {'bootstrap.servers': 'localhost:29092', 'group.id': 'default-demo'}
  {'bootstrap.servers': 'localhost:29091', 'group.id': 'demo', 'security.protocol': 'SASL_SSL', 'sasl.mechanism': 'PLAIN', 'sasl.username': 'myuser', 'sasl.password': 'mypass'}

Variable return values
-----------------

It may be the case that your handler function returns zero or more values. In that case, ``yield`` can be used instead of ``return``.

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

Interval
------------------

The following snippet prints out localtime every second:

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
- Out handler function prints out the local time whenever it's called

::

  23:25:10
  23:25:11
  23:25:12
  ...
