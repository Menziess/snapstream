Snapstream documentation
========================

Snapstream provides a pure python data-flow model that works with anything:

- Any `iterable <https://pythonbasics.org/iterable/>`_ can act as a source of data
- Any callable may act as a sink
- Handler functions can subscribe to iterables using the ``snap`` decorator

::

  from snapstream import snap, stream

  @snap(range(2), sink=[print])
  def handler(msg):
      yield f'Hello {msg}'

  stream()

- Upon calling ``stream()``, each iterable is processed in a separate thread
- Each element in the iterable is published to all subscriber functions

::

  Hello 0
  Hello 1

Stateful Streaming
------------------

Snapstream aims to be unopinionated, whilst being extensible and having sensible default tools:

.. currentmodule:: snapstream

.. autosummary::
   Topic
   Cache
   Conf

.. autoclass:: Topic
.. autoclass:: Cache
.. autoclass:: Conf

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   examples

.. toctree::
   :maxdepth: 1
   :caption: Modules:

   modules

Indices and tables
------------------

* :ref:`genindex`
