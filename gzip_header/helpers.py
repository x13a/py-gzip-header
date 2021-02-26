import functools
import itertools
from typing import Protocol

CSTR_ZERO = b'\0'
ENCODING = 'latin-1'


class ReaderProtocol(Protocol):
    def read(self, size: int) -> bytes:
        raise NotImplementedError


class Reader:
    def __init__(self, reader: ReaderProtocol):
        self._reader = reader
        self._buf = bytearray()

    def read(self, size: int) -> bytes:
        data = self._reader.read(size)
        if len(data) != size:
            raise EOFError('read size mismatch')
        self._buf.extend(data)
        return data


def read_cstr(reader: Reader) -> str:
    return b''.join(itertools.takewhile(
        CSTR_ZERO.__ne__,
        iter(functools.partial(reader.read, 1), CSTR_ZERO),
    )).decode(ENCODING)
