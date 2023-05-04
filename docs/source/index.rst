.. _index:

Snapstream documentation
========================

Snapstream provides a pure python data-flow model that works well with built-in objects.

- Any `iterable <https://pythonbasics.org/iterable/>`_ may act as a source of data
- Any callable can be used as a sink
- Functions can subscribe to iterables using the ``snap`` decorator

::

  from snapstream import snap, stream

  @snap(range(2), sink=[print])
  def handler(msg):
      yield f'Hello {msg}'

  stream()

- When we call ``stream()``, each iterable is processed in a separate thread
- Elements from the iterables are published to their subscriber functions

::

  Hello 0
  Hello 1

Stateful Streaming
------------------

By combining the default tools below with this data-flow model, it is relatively easy to establish complex stateful streams (see :ref:`Examples <examples>`):

.. currentmodule:: snapstream

.. autosummary::
   Topic
   Cache
   Conf

.. autoclass:: Topic
   :noindex:
.. autoclass:: Cache
   :noindex:
.. autoclass:: Conf
   :noindex:

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
