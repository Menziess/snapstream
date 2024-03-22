.. _testing:

Testing
=======

The following snippet is out ``main.py`` file. Let's say that we want to test our ``produce`` and ``consume`` handler functions as shown in the :ref:`kafka` example. Let's also throw a Cache in there:

::

  from snapstream import Cache, Topic, snap, stream

  from time import sleep

  messages = ('🏆', '📞', '🐟', '👌')

  c = Cache('db')
  t = Topic('emoji', {
      'bootstrap.servers': 'localhost:29091',
      'auto.offset.reset': 'earliest',
      'group.instance.id': 'demo',
      'group.id': 'demo',
  })

  @snap(messages, sink=[t, c])
  def produce(msg):
      sleep(0.5)
      print(f'producing {msg}')
      yield msg, msg

  @snap(t, sink=[print])
  def consume(msg):
      val = msg.value().decode()
      return f'got: {val}'

  stream()


Avoiding Side Effects
---------------------

It's good practice to avoid triggering side effects when invoking a script by putting code with side effects in the following block:

::

  c = Cache('db')  # this triggers the 'db' folder to be created

  if __name__ == "__main__":
      # Things that should not run when importing from, or running tests in this module
      pass

Mocking
-------

This test example -- let's call it ``test_main.py`` -- uses ``pytest-mock`` (`mocker` fixture).

It uses:

- **FakeMessage:** allows us to pass some value that our code can get using the ``.value()`` method, just like a Kafka message
- **FakeCache:** allows us to replace a cache with a defaultdict that also has the ``.values()`` method
- **test_produce:** mocks the Cache and Topic, calls the function under test, then asserts that the topic was called with the correct output

::

  from main import produce


  class FakeMessage:

      def __init__(self, return_value):
          self.return_value = return_value

      def value(self):
          return self.return_value

      def timestamp(self):
          return (1, dt.now().timestamp() * 1000)


  class FakeCache(defaultdict):

      def __init__(self, contents={}):
          return super().__init__(lambda: None, contents)

      def __call__(self, key, val, *args) -> None:
          self.__setitem__(key, val)

      def values(self, *args, **kwargs):
          return [_ for _ in super().values() if _]


  def test_produce(mocker):
      """Should produce message to kafka topic."""
      topic = mocker.stub(name='topic')
      cache = FakeCache()
      mocker.patch('snapstream.Topic.__call__', topic)
      mocker.patch('main.c', cache)

      produce(FakeMessage('🏆', {}))  # type: ignore

      # Assert that cache was updated
      assert cache['🏆'] == '🏆'

      # Check if expected key and val have been produced
      key, val = '🏆', '🏆'
      topic.assert_called_once_with(key=key, val=val)
