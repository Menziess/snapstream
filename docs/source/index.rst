.. _index:

Snapstream documentation
========================

Snapstream can be summarized as:

- ``Topic``: default way to interact with kafka
- ``Cache``: default persistence functionality
- ``snap`` and ``stream``: a data-flow model used to parallelize stream processing

A typical hello-world application would look something like this:

::

  from snapstream import snap, stream

  messages = ('🏆', '📞', '🐟', '👌')


  @snap(iter(messages), sink=[print])
  def produce(msg):
      return f'Hello {msg}!'


  stream()

::

  Hello 🏆!
  Hello 📞!
  Hello 🐟!
  Hello 👌!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   kafka
   install
   examples
   testing
   cli

.. toctree::
   :maxdepth: 1
   :caption: Modules:

   modules

Indices and tables
------------------

* :ref:`genindex`
