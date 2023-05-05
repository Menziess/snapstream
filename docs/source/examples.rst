.. _examples:

Examples
============

Here's a list of useful snippets. Couldn't find what you seek? Create a `new issue <https://github.com/Menziess/snapstream/issues/new>`_.

Conf
-------

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

Topic
-------

Topic can be used to consume and produce to a kafka.

Spin up a local kafka broker using `docker-compose.yml <https://github.com/Menziess/snapstream/blob/master/docker-compose.yml>`_:

.. code-block:: bash

  docker compose up broker -d

- Connect to the "emoji" topic via ``localhost:29091``
- A message is sent to kafka by calling ``topic`` as a function

::

  from snapstream import Topic

  topic = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  }, offset=-2)

  topic('👌')

  for msg in topic:
      print(msg.value().decode())

- Messages are consumed when iterated over ``topic``

::

  👌

(using snapstream)
******************

The following code runs in parallel:

::

  from time import sleep

  from snapstream import Topic, snap, stream

  messages = ('🏆', '📞', '🐟', '👌')
  topic = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  })

  @snap(messages, sink=[topic])
  def produce(msg):
      sleep(0.1)
      yield msg

  @snap(topic, sink=[print])
  def consume(msg):
      yield msg.value().decode()

  stream()

::

  🏆
  📞
  🐟
  👌

Cache
-------

::

  # TODO

Yield over return
---------------
::

  # TODO

Joining Streams
---------------

::

  # TODO

Timer
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
