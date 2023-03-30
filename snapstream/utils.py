"""Snapstream utilities."""

import logging
from typing import Any, Dict


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
