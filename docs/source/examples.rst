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
