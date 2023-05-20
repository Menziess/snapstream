"""Snapstream utilities."""

import logging
from os import environ, getenv, listdir
from pathlib import Path
from re import match, sub
from typing import Any, Dict, Optional

from toolz.curried import compose, curry, last

logger = logging.getLogger(__name__)


def get_variable(
    secret: str,
    secrets_base_path='',
    required=False
) -> Optional[str]:
    """Get environment or file variable."""
    def getfilesecret(filepath):
        with filepath.open('r') as f:
            return f.read()
    filepath = Path(secrets_base_path) / secret
    try:
        return getenv(secret) or (
            getfilesecret(filepath)
            if secrets_base_path else None
        )
    except FileNotFoundError as e:
        logger.warning(
            f'Environment variable "{secret}" or file: '
            f'"{filepath}" not found (optional={not required}).')
        if required:
            raise e
        return None


def get_prefixed_variables(
    prefix: str,
    secrets_base_path='',
    key_sep='.'
) -> dict:
    """Get environment or file variables having prefix.

    >>> environ['DEFAULT_EXAMPLE'] = 'test'
    >>> get_prefixed_variables(prefix='DEFAULT_')
    {'example': 'test'}
    >>> del environ['DEFAULT_EXAMPLE']
    """
    candidates = list(environ)
    try:
        candidates += listdir(secrets_base_path) if secrets_base_path else []
    except FileNotFoundError as e:
        logger.warning((
            f"Function `{get_prefixed_variables.__name__}()` can't "
            f"look up file secrets: {e}."
        ))
    filter_func = compose(
        curry(match)(prefix.lower()),
        str.lower
    )
    matches = filter(filter_func, candidates)
    normalize_name = compose(
        curry(sub)('[^0-9a-zA-Z]+', key_sep),
        str.lower
    )
    variables = {
        last(
            normalize_name(name)
            .split(normalize_name(prefix))
        ): get_variable(name, secrets_base_path)
        for name in matches
    }
    return variables


def folder_size(folder: str, unit='mb'):
    """Get size of folder."""
    exponents_map = {'bytes': 0, 'kb': 1, 'mb': 2, 'gb': 3}
    return round(
        sum(f.stat().st_size for f in Path('.').glob(folder) if f.is_file())
        / 1024 ** exponents_map[unit],
        3
    )


class Singleton(type):
    """Maintain a single instance of a class."""

    _instances: Dict['Singleton', Any] = {}

    def __init__(cls, name, bases, dct):
        """Perform checks before instantiation."""
        if '__update__' not in dct:
            raise TypeError('Expected __update__.')

    def __call__(cls, *args, **kwargs):
        """Apply metaclass singleton action."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        instance = cls._instances[cls]
        instance.__update__(*args, **kwargs)
        return instance


class KafkaIgnoredPropertyFilter(logging.Filter):
    """Filter out specific kafka logging."""

    def filter(self, record):
        """Suppress CONFWARN messages with specific config keys."""
        return not (
            (record.levelno == logging.WARNING)
            and
            'property and will be ignored' in record.getMessage()
        )
