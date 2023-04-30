Snapstream documentation
======================================

Hi there! Glad to make your acquaintance.
I'll be your guide for the next 2 minutes, walking you through some code samples to explain what the rather terse description of snapstream means:

.. epigraph::

   **Snapstream provides a data-flow model to simplify development of stateful streaming applications.**

As a start, let's process the iterable ``range(5)``, just to get familiar with some core concepts:

::

  from snapstream import snap, stream

  @snap(range(2), sink=[print])
  def handler(msg):
      yield f'Hello {msg}'

  stream()

When ``stream()`` is called, the messages flow through the handler function into the sink.

::

  Hello 0
  Hello 1

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   source/install
   autoapi/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
