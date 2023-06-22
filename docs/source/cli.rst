.. _cli:

CLI
============

The snapstream cli tool allows you to inspect any ``Topic`` or ``Cache``:

::

  snapstream --help

When providing an action; `topic` or `cache`, the configurations can be saved to a config file; `~/.snapstreamcfg`, which may look like this:

::

  [
    {
        "type": "Topic",
        "name": "demo",
        "conf": {
            "bootstrap.servers": "localhost:29091",
            "sasl.username": "\\$ConnectionString",
            "sasl.password": "$MY_PASSWORD"
        }
    }
  ]

Environment variables may be referenced by prepending the ``$`` character. Which can be escaped by prepending ``\\`` in front of ``$``.

Cache
-----

Starting off with a cache that has a single entry:

::

  from snapstream import Cache

  c = Cache('db')

  c['123'] = {'timestamp': 123, 'value': 'A story about jack and james.'}

There are several ways to query the cache:

::

  snapstream cache db            # show all values in cache
  snapstream cache db -k "123"   # values where key is "123"
  snapstream cache db -k "^\d"   # values where key starts with a digit

Regular expressions also work on values:

::

  snapstream cache db -v "^(?=.*?\bjack\b).*?\bjames\b.*"

::

  >>> key: 123
  {'timestamp': 123, 'value': 'A story about jack and james.'}

Fields can be filtered when a dictionary is returned:

::

  snapstream cache db -c "value,"  # column names are comma separated

::

  >>> key: 123
  {'value': 'A story about jack and james.'}

To get some additional RocksDB statistics on the cache, pass the ``--stats`` flag:

::

  snapstream cache db --stats

::

  >>> key: 123
  {'timestamp': 123, 'value': 'A story about jack and james.'}

  Statistics:
  [
      {
          "name": "/000009.sst",
          "size": 1059,
          "level": 0,
          "start_key": "123",
          "end_key": "123",
          "num_entries": 1,
          "num_deletions": 0
      }
  ]
  Folder size: 0.034 mb

Topic
-----

The same filtering logic applies for topics.

Pass an avro schema filepath to deserialize avro messages:

::

  snapstream topic my-topic --schema schemas/my-schema.avsc

::

  >>> timestamp: 2023-05-20T12:00:00.000000+00:00
  >>> offset: 0
  >>> key: '123'
  {'value': 'A story about jack and james.'}

Start reading from a given offset:

::

  snapstream topic my-topic -o -1  # read from latest (default)
  snapstream topic my-topic -o -2  # read from start
  snapstream topic my-topic -o 33  # read from specific offset

::

  >>> timestamp: 2023-05-20T12:00:00.000000+00:00
  >>> offset: 33
  >>> key: '456'
  {'timestamp': 156, 'value': 'They discovered two pillars and a stairway.'}


The ``--stats`` flag is not available for topics.
