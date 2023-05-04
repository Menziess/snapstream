.. _examples:

Examples
============

We may have multiple iterables, multiple handler functions, and multiple sinks:

::

  from snapstream import snap, stream
  from time import sleep

  it = ('🏆', '📞', '🐟', '👌')

  @snap(it, sink=[print])
  def handler1(msg):
      sleep(0.1)
      yield '1' + msg

  @snap(it, sink=[print])
  def handler2(msg):
      sleep(0.1)
      yield '2' + msg

  @snap(it, sink=[print, print])
  def handler3(msg):
      sleep(0.1)
      yield '3' + msg

  stream()

Upon starting the stream, you may see something like this:

::

  1🏆
  2🏆
  3🏆
  3🏆
  1📞
  2📞
  3📞
  3📞
  1🐟
  2🐟
  3🐟
  3🐟
  1👌
  2👌
  3👌
  3👌

The two iterables are processed in parallel.

To tell you something about the backstory of this project, and the problem it tries to solve; it's actually quite difficult to join or merge kafka streams.
When you finally bump into a great framework that solves this problem, you may find that it only works when the data is consumed from a single kafka cluster,
or that it shoehorns you into using certain syntax or patterns that you didn't intend to use.
My opinion is that libraries should provide you with tools, and that you should always be in control.


In a simple world, each message in a stream is simply sent from point A to point B.
But when data has to be joined/merged from multiple topics (especially when these topics live on separate kafka clusters), things tend to get more complicated.
In these cases, sequential processing by subscribing a single consumer to multiple topics won't work.

That's where the "data-flow model" comes in.

As a result, messages may need to be processed in parallel, requiring a thread-safe caching technology.


Let's have a look at some "tools" first, and then I'll show you where the "data-flow model" comes in:

* .. class:: Topic(name: str, conf: dict = {}, ...)

  Topic is used to consume from (iterable), and produce to (callable) kafka using `confluent-kafka <https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html/>`_:

  ::

    from snapstream import Topic

    topic = Topic('emoji', {
        'bootstrap.servers': 'localhost:29091',
        'group.id': 'demo'
    })

  Example:

    >>> topic({'emoji': '🏆'})
    >>> for msg in topic:
    ...     print(msg)
    🏆

::

  from snapstream import Topic, Cache, snap, stream

  @snap(range(5), sink=[print])
  def handler(msg):
      yield f'Hello {msg}'

  stream()
