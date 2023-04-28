"""Snapstream CLI tool."""

from argparse import ArgumentParser, Namespace
from datetime import datetime as dt
from datetime import timezone
from json import dump, load
from os import path
from re import search
from sys import argv, exit
from typing import Optional

from toolz import curry

from snapstream import READ_FROM_END, Topic
from snapstream.codecs import AvroCodec

DEFAULT_CONFIG_PATH = '~/'
CONFIG_FILENAME = '.snapstreamcfg'


def get_args(args=argv[1:]):
    """Get user arguments."""
    parser = ArgumentParser('snapstream')
    subparsers = parser.add_subparsers(dest='action', required=True)
    parser.add_argument('--config-path', type=str, default=DEFAULT_CONFIG_PATH,
                        help='file containing topic/cache configurations')
    parser.add_argument('--secrets-base-path', type=str, default='',
                        help='folder containing secret files')

    topic = subparsers.add_parser('topic', help='read messages from Topic')
    topic.add_argument('name', type=str,
                       help='topicname')
    topic.add_argument('-s', '--schema', type=str,
                       help='path to avro schema file')
    topic.add_argument('-k', '--key-filter', type=str,
                       help='regex used to filter messages by key')
    topic.add_argument('-v', '--val-filter', type=str,
                       help='regex used to filter messages by value')
    topic.add_argument('-c', '--columns', type=str,
                       help='list of columns to extract from message, ex: "time,date,pk"')
    topic.add_argument('-o', '--offset', type=int, default=READ_FROM_END,
                       help='offset to start reading from, ex: -2/-1/3025 (start/end/other)')

    cache = subparsers.add_parser('cache', help='read records from Cache')
    cache.add_argument('path', type=str, help='path of the cache files')

    return parser.parse_args(args)


def default_topic_entry(name: str) -> dict:
    """Create default topic entry."""
    return {
        'type': 'Topic',
        'name': name,
        'conf': {
            'bootstrap.servers': 'localhost:29091',
        }
    }


def default_cache_entry(path: str) -> dict:
    """Create default topic entry."""
    return {
        'type': 'Cache',
        'name': path,
        'conf': {}
    }


def find_or_add_entry(config_path: str, args: Namespace):
    """Update config file."""
    try:
        with open(config_path) as f:
            config = load(f)
        if not (isinstance(config, list) and all(isinstance(el, dict) for el in config)):
            raise RuntimeError('Expected config to be a json list:', config)
    except FileNotFoundError:
        if not (
            input(f'Create {config_path} config? [y/n]: ')
            .upper()
            .startswith('Y')
        ):
            exit()
        config = []

    # Find prop having certain key
    prop = {
        'topic': 'name',
        'cache': 'path',
    }[args.action]
    key = getattr(args, prop)
    if entry := {
        key: _
        for _ in config
        if _[prop] == key
    }.get(key):
        return entry

    # If not found, create entry
    entry = (
        default_topic_entry(args.name) if args.action == 'topic'
        else default_cache_entry(args.path) if args.action == 'cache'
        else {}
    )
    config.append(entry)
    with open(config_path, 'w') as f:
        dump(config, f, indent=4)
    return entry


def regex_filter(regex: str, key: Optional[str]) -> bool:
    """Check whether key matches regex filter."""
    if regex and key:
        return bool(search(regex, key))
    if regex and not key:
        raise RuntimeError('Can\'t filter topic without keys.')
    return True


def inspect_topic(conf: dict, args: Namespace):
    """Read messages from topic."""
    if 'group.id' not in conf:
        conf['group.id'] = '$Default'
    if 'group.instance.id' not in conf:
        conf['group.instance.id'] = '$Default'

    schema = AvroCodec(args.schema) if args.schema else None
    key_filter = curry(regex_filter)(args.key_filter)
    val_filter = curry(regex_filter)(args.val_filter)

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


def inspect_cache(conf: dict, args: Namespace):
    """Read records from cache."""
    raise NotImplementedError('Not yet implemented.')


def main():
    """Run main program."""
    args = get_args()
    try:
        # Construct config path
        config_path = path.join(
            path.expanduser(args.config_path)
            if args.config_path.startswith('~')
            else args.config_path, CONFIG_FILENAME
        )

        # Get entry from config
        entry = find_or_add_entry(config_path, args)

        # Call appropriate function with config and args
        {
            'topic': inspect_topic,
            'cache': inspect_cache,
        }[args.action](entry['conf'], args)
    except KeyboardInterrupt:
        print('\nYou stopped the program.')


if __name__ == "__main__":
    main()
