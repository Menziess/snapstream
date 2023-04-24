"""Snapstream CLI tool."""

from argparse import ArgumentParser, Namespace
from datetime import datetime as dt
from datetime import timezone
from re import search
from sys import argv
from typing import Optional

from toolz import curry

from snapstream import READ_FROM_END, Conf, Topic
from snapstream.codecs import AvroCodec
from snapstream.utils import get_prefixed_variables


def get_args(args=argv[1:]):
    """Get user arguments."""
    parser = ArgumentParser('snapstream')
    subparsers = parser.add_subparsers(dest='action', required=True)

    topic = subparsers.add_parser('topic', help='Read messages from topic.')
    topic.add_argument('name', type=str,
                       help='Name of the topic to consume from.')
    topic.add_argument('-s', '--schema', type=str,
                       help='Path to avro schema file.')
    topic.add_argument('-k', '--key-filter', type=str,
                       help='Regex used to filter messages by key.')
    topic.add_argument('-v', '--val-filter', type=str,
                       help='Regex used to filter messages by value.')
    topic.add_argument('-c', '--columns', type=str,
                       help='A list of column names, ex: "time,date,pk".')
    topic.add_argument('-o', '--offset', type=int, default=READ_FROM_END,
                       help='Use -2/-1 to read from start/end respectively.')

    cache = subparsers.add_parser('cache', help='Read records from cache.')
    cache.add_argument('path', type=str, help='Path of the cache files.')

    return parser.parse_args(args)


def regex_filter(regex: str, key: Optional[str]) -> bool:
    """Check whether key matches regex filter."""
    if regex and key:
        return bool(search(regex, key))
    if regex and not key:
        raise RuntimeError('Can\'t filter topic without keys.')
    return True


def inspect_topic(args: Namespace):
    """Read messages from topic."""
    args = get_args()
    Conf(get_prefixed_variables('DEFAULT_'))
    conf = get_prefixed_variables(args.name)

    if 'group.id' not in conf:
        conf['group.id'] = '$Default'
    if 'group.instance.id' not in conf:
        conf['group.instance.id'] = '$Default'

    schema = AvroCodec(args.schema) if args.schema else None
    key_filter = curry(regex_filter)(args.key_filter)
    val_filter = curry(regex_filter)(args.val_filter)

    try:
        for msg in Topic(args.name, conf, args.offset, schema):
            timestamp = (
                dt
                .fromtimestamp(msg.timestamp()[-1] / 1000, tz=timezone.utc)
                .isoformat()
                if msg.timestamp() else ''
            )
            key = msg.key().decode() if msg.key() is not None else ''
            offset = msg.offset()
            val = msg.value()
            if key_filter(str(key)) and val_filter(str(val)):
                print()
                print('>>> timestamp:', timestamp)
                print('>>> offset:', offset)
                print('>>> key:', key)
                print(val) if not args.columns else print({
                    k: v for k, v in val.items() if k in args.columns.split(',')
                })
    except KeyboardInterrupt:
        print('You stopped the program.')


def inspect_cache(args: Namespace):
    """Read records from cache."""
    raise NotImplementedError('Not yet implemented.')


def main():
    """Run main program."""
    args = get_args()
    {
        'topic': inspect_topic,
        'cache': inspect_cache,
    }[args.action](args)


if __name__ == "__main__":
    main()
