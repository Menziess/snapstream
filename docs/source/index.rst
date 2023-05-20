.. _index:

Snapstream documentation
========================

Snapstream can be summarized as:

- Two functions: ``snap`` and ``stream`` (the data-flow model)
- ``Topic``: default way to interact with kafka
- ``Cache``: default persistence functionality

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

These simple concepts offer interesting ways to establish complex stateful streams.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   examples
   cli

.. toctree::
   :maxdepth: 1
   :caption: Modules:

   modules

Indices and tables
------------------

* :ref:`genindex`
