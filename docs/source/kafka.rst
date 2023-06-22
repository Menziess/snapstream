.. _index:

Kafka
=====

When we introduce kafka, this is what it looks like:

::

  from time import sleep

  from snapstream import Topic, snap, stream

  messages = ('🏆', '📞', '🐟', '👌')

  t = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'auto.offset.reset': 'earliest',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  })

  @snap(messages, sink=[t])
  def produce(msg):
      sleep(0.5)
      print(f'producing {msg}')
      return msg

  @snap(t, sink=[print])
  def consume(msg):
      val = msg.value().decode()
      return f'got: {val}'

  stream()

- Any `iterable <https://pythonbasics.org/iterable/>`_ may act as a source of data
- Any callable can be used as a sink

.. image:: ../../res/demo.gif

- When we call ``stream()``, each iterable is processed in a separate thread
- Elements are published to each ``snap`` decorated handler function

::

  Producing 🏆
  got: 🏆
  Producing 📞
  got: 📞
  Producing 🐟
  got: 🐟
  Producing 👌
  got: 👌

These simple concepts offer interesting ways to establish complex arbitrary stateful streams.

**Note:** out of the box advanced features such as `synchronizing streams <https://menziess.github.io/howto/use/snapstream>`_  could be offered in the future, feel free to `contribute <https://github.com/Menziess/snapstream/pulse>`_!
