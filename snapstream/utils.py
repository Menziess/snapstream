"""Snapstream utilities."""

import logging
from os import environ, getenv, listdir
from pathlib import Path
from re import match, sub
from typing import Any, Dict, Optional

from toolz.curried import compose, curry

logger = logging.getLogger(__name__)


def get_variable(
    secret: str,
    secrets_base_path='/etc/secrets',
    required=False
) -> Optional[str]:
    """Get environment or file variable."""
    def getfilesecret(filepath):
        with filepath.open('r') as f:
            return f.read()
    filepath = Path(secrets_base_path) / secret
    try:
        return getenv(secret) or getfilesecret(filepath)
    except FileNotFoundError as e:
        logger.warning(
            f'Environment variable "{secret}" or file: '
            f'"{filepath}" not found (optional={not required}).')
        if required:
            raise e
        return None


def get_prefixed_variables(
    prefix: str,
    secrets_base_path='/etc/secrets',
    key_sep='.'
) -> dict:
    """Get environment or file variables having prefix.

    >>> environ['TEST_EXAMPLE'] = 'test'
    >>> get_secrets_dict(prefix='TEST')
    {'test.example': 'test'}
    >>> del environ['TEST_EXAMPLE']
    """
    candidates = list(environ)
    try:
        candidates += listdir(secrets_base_path)
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
        normalize_name(name): get_variable(name, secrets_base_path)
        for name in matches
    }
    return variables


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
            record.levelno == logging.WARNING
            and 'property and will be ignored' in record.getMessage()
        )
