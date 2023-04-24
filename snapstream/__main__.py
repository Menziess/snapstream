"""Snapstream CLI tool."""

import logging
from argparse import ArgumentParser
from sys import argv

from snapstream.codecs import AvroCodec
from snapstream.core import READ_FROM_END, get_consumer
from snapstream.utils import get_prefixed_variables

BASIC_FORMAT = '%(levelname)s:%(name)s:%(message)s'


def get_args(args=argv[1:]):
    """Get user arguments."""
    parser = ArgumentParser('snapstream')
    parser.add_argument('-t', '--topic', type=str, required=True,
                        help='Name of the topic to consume from.')
    parser.add_argument('-s', '--schema', type=str,
                        help='Path to avro schema.')
    parser.add_argument('-o', '--offset', type=int, default=READ_FROM_END,
                        help='Use -2/-1 to read from start/end respectively.')
    parser.add_argument('--loglevel', type=str, default='info',
                        help='Provide log level. Example --loglevel debug.')
    parser.add_argument('--logformat', type=str, default=BASIC_FORMAT,
                        help=f'Format used by logger (ex: {BASIC_FORMAT}).')
    return parser.parse_args(args)


def main():
    """Run main program."""
    args = get_args()
    logging.basicConfig(format=args.logformat, level=args.loglevel.upper())
    conf = get_prefixed_variables(args.topic)

    if 'group.id' not in conf:
        conf['group.id'] = '$Default'

    schema = AvroCodec(args.schema) if args.schema else None

    with get_consumer(args.topic, conf, args.offset, schema) as consumer:
        for msg in consumer:
            print(msg)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
