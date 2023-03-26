"""Snapstream codecs."""

from abc import ABCMeta, abstractmethod
from typing import Any


class Codec(metaclass=ABCMeta):
    """Base class for codecs."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name property."""
        ...

    @name.setter
    def name(self, name) -> None:
        self.name = name

    @name.getter
    def name(self) -> str:
        return self.name

    @abstractmethod
    def encode(self, obj: Any) -> bytes:
        """Serialize object."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, s: bytes) -> dict:
        """Deserialize object."""
        raise NotImplementedError
