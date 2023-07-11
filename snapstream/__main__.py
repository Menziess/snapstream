"""Snapstream CLI tool.

This tool can be used to inspect kafka streams or rocksdb databases.
"""

from argparse import ArgumentParser, Namespace
from datetime import datetime as dt
from datetime import timezone
from json import dump, dumps, load
from os import path
from re import search
from sys import argv, exit
from typing import Callable, Optional

from rocksdict import AccessType
from toolz import compose, curry, identity

from snapstream import READ_FROM_END, Cache, Topic
from snapstream.codecs import AvroCodec
from snapstream.utils import folder_size, get_variable

DEFAULT_CONFIG_PATH = '~/'
CONFIG_FILENAME = '.snapstreamcfg'


def get_args(args=argv[1:]) -> Namespace:
    """Get user arguments."""
    parser = ArgumentParser('snapstream')
    subparsers = parser.add_subparsers(dest='action', required=True)
    parser.add_argument('--config-path', type=str, default=DEFAULT_CONFIG_PATH,
                        help='file containing topic/cache configurations')
    parser.add_argument('--secrets-base-path', type=str, default='/etc/secrets',
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
    cache.add_argument('-k', '--key-filter', type=str,
                       help='regex used to filter records by key')
    cache.add_argument('-v', '--val-filter', type=str,
                       help='regex used to filter records by value')
    cache.add_argument('-c', '--columns', type=str,
                       help='list of columns to extract from message (if dict), ex: "time,date,pk"')
    cache.add_argument('--stats', action='store_true',
                       help='print additional database statistics')

    return parser.parse_args(args)


def default_topic_entry(args: Namespace, prep: Callable) -> dict:
    """Create default topic entry."""
    return {
        'type': 'Topic',
        'name': prep(args.name),
        'conf': {
            'bootstrap.servers': 'localhost:29091',
        },
        'schema_path': args.schema,
        'secrets_base_path': args.secrets_base_path
    }


def default_cache_entry(args: Namespace, prep: Callable) -> dict:
    """Create default topic entry."""
    return {
        'type': 'Cache',
        'path': prep(args.path),
        'conf': {}
    }


def get_config_entry(config_path: str, args: Namespace) -> dict:
    """Update config file."""
    try:
        with open(config_path) as f:
            config = load(f)
        if not (isinstance(config, list) and all(isinstance(el, dict) for el in config)):
            raise RuntimeError('Expected config to be a json list:', config)
    except FileNotFoundError:
        if not (
            input(f'Create missing {config_path}? [y/n]: ')
            .upper()
            .startswith('Y')
        ):
            exit()
        config = []

    # Find prop having certain key
    prep, prop = {
        'topic': [identity, 'name'],
        'cache': [compose(path.abspath, path.expanduser), 'path'],
    }[args.action]
    key = getattr(args, prop)
    if entry := {
        key: _
        for _ in config
        if _.get(prop) == prep(key)
    }.get(key):
        return entry

    # If not found, create entry
    entry = (
        default_topic_entry(args, prep) if args.action == 'topic'
        else default_cache_entry(args, prep) if args.action == 'cache'
        else {}
    )
    config.append(entry)
    with open(config_path, 'w') as f:
        dump(config, f, indent=4)
    return entry


def replace_variable_references(entry: dict, args: Namespace) -> dict:
    """For every value starting with $, replace with env."""
    conf = entry['conf']
    for k, v in conf.items():
        if v.startswith('$'):
            conf[k] = get_variable(v[1:], args.secrets_base_path)
        if v.startswith(r'\$'):
            conf[k] = v.replace(r'\$', '$')
    entry['conf'] = conf
    return entry


def regex_filter(regex: str, key: Optional[str]) -> bool:
    """Check whether key matches regex filter."""
    if regex and key:
        return bool(search(regex, key))
    if regex and not key:
        raise RuntimeError('Can\'t filter topic without keys.')
    return True


def inspect_topic(entry: dict, args: Namespace):
    """Read messages from topic."""
    conf = entry['conf']
    if 'group.id' not in conf:
        conf['group.id'] = '$Default'
    if 'group.instance.id' not in conf:
        conf['group.instance.id'] = '$Default'

    start_time = dt.now(tz=timezone.utc)
    schema_path = args.schema or entry.get('schema_path')
    schema = AvroCodec(args.schema) if schema_path else None
    key_filter = curry(regex_filter)(args.key_filter)
    val_filter = curry(regex_filter)(args.val_filter)

    for msg in Topic(args.name, conf, args.offset, schema):
        if msg.timestamp():
            timestamp = (
                dt
                .fromtimestamp(msg.timestamp()[-1] / 1000, tz=timezone.utc)
            )
            timestamp_str = timestamp.isoformat()
        else:
            timestamp, timestamp_str = None, ''
        key = msg.key().decode() if msg.key() is not None else ''
        offset = msg.offset()
        val = msg.value()
        if key_filter(str(key)) and val_filter(str(val)):  # pyright: ignore
            print()
            if timestamp and timestamp < start_time:
                print('>>> timestamp:', timestamp_str, '(catching up)')
            else:
                print('>>> timestamp:', timestamp_str)
            print('>>> offset:', offset)
            print('>>> key:', key)
            print(val) if not args.columns else print({
                k: v for k, v in val.items() if k in args.columns.split(',')
            })


def inspect_cache(entry: dict, args: Namespace):
    """Read records from cache."""
    if not path.isdir(args.path):
        raise OSError(f'Folder doesn\'t exist: {args.path}')
    cache = Cache(
        args.path,
        access_type=AccessType.read_only(),
    )
    key_filter = curry(regex_filter)(args.key_filter)
    val_filter = curry(regex_filter)(args.val_filter)
    for key, val in cache.items():
        if key_filter(str(key)) and val_filter(str(val)):  # pyright: ignore
            if args.columns and not isinstance(val, dict):
                raise ValueError(f'Columns could not be extracted from {type(val)}: {val}')
            print()
            print('>>> key:', key)
            print(val) if not args.columns else print({
                k: v for k, v in val.items() if k in args.columns.split(',')
            })

    if args.stats:
        print()
        print('Statistics:')
        print(dumps(cache.live_files(), indent=4))
        print('Folder size:', folder_size(args.path + '/**/*', 'mb'), 'mb')


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
        entry = get_config_entry(config_path, args)
        entry = replace_variable_references(entry, args)

        # Call appropriate function with config and args
        {
            'topic': inspect_topic,
            'cache': inspect_cache,
        }[args.action](entry, args)
    except KeyboardInterrupt:
        print('\nYou stopped the program.')


if __name__ == "__main__":
    main()
