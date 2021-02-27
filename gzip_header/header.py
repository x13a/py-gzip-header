"""
https://tools.ietf.org/html/rfc1952
"""

from __future__ import annotations

import gzip
import struct
import zlib
from dataclasses import dataclass
from typing import (
    List,
    Optional,
)

from .helpers import (
    CSTR_ZERO,
    ENCODING,
    Reader,
    ReaderProtocol,
    read_cstr,
)

MAGIC = bytes([0x1f, 0x8b])
PARAMS_FMT = '<BBIBB'
BYTE_ORDER = 'little'

MAGIC_LEN = 2
PARAMS_LEN = 8
SIZE_LEN = 2
CHECKSUM_LEN = 2


@dataclass(init=False)
class Field:
    ids: bytes
    data: bytes

    def __init__(self, ids: bytes, data: bytes):
        if len(ids) != MAGIC_LEN:
            raise gzip.BadGzipFile(
                f'fextra ids len should be {MAGIC_LEN} bytes')
        self.ids = ids
        self.data = data

    def __bytes__(self) -> bytes:
        assert len(self.ids) == MAGIC_LEN
        return (
            self.ids +
            len(self.data).to_bytes(SIZE_LEN, BYTE_ORDER) +
            self.data
        )


@dataclass
class Header:
    cm: int = 8
    flg: int = 0
    mtime: int = 0
    xfl: int = 0
    os: int = 255
    _fextra: Optional[List[Field]] = None
    _fname: Optional[str] = None
    _fcomment: Optional[str] = None

    @classmethod
    def from_reader(cls, reader: ReaderProtocol) -> Header:
        reader = Reader(reader)
        magic = reader.read(MAGIC_LEN)
        if magic != MAGIC:
            raise gzip.BadGzipFile('invalid magic bytes')
        cm, flg, mtime, xfl, os = struct.unpack(
            PARAMS_FMT,
            reader.read(PARAMS_LEN),
        )
        res = cls(
            cm=cm,
            flg=flg,
            mtime=mtime,
            xfl=xfl,
            os=os,
            _fextra=cls._parse_fextra(reader) if flg & gzip.FEXTRA else None,
            _fname=read_cstr(reader) if flg & gzip.FNAME else None,
            _fcomment=read_cstr(reader) if flg & gzip.FCOMMENT else None,
        )
        if (
            flg & gzip.FHCRC and
            cls._calc_checksum(bytes(reader._buf)) != reader.read(CHECKSUM_LEN)
        ):
            raise gzip.BadGzipFile('checksum mismatch')
        return res

    @property
    def fextra(self) -> Optional[List[Field]]:
        return self._fextra

    @fextra.setter
    def fextra(self, value: Optional[List[Field]]):
        self._fextra = value
        self._set_flg(gzip.FEXTRA, value is not None)

    @property
    def fname(self) -> Optional[str]:
        return self._fname

    @fname.setter
    def fname(self, value: Optional[str]):
        self._fname = value
        self._set_flg(gzip.FNAME, value is not None)

    @property
    def fcomment(self) -> Optional[str]:
        return self.fcomment

    @fcomment.setter
    def fcomment(self, value: Optional[str]):
        self._fcomment = value
        self._set_flg(gzip.FCOMMENT, value is not None)

    @staticmethod
    def _parse_fextra(reader: Reader) -> List[Field]:
        xlen = int.from_bytes(reader.read(SIZE_LEN), BYTE_ORDER)
        fields = []
        size = MAGIC_LEN + SIZE_LEN
        while xlen > 0:
            ids, data_len = struct.unpack(
                f'<{MAGIC_LEN}sH',
                reader.read(size),
            )
            fields.append(Field(
                ids=ids,
                data=reader.read(data_len)
            ))
            xlen -= data_len + size
        return fields

    @staticmethod
    def _calc_checksum(data: bytes) -> bytes:
        return zlib.crc32(data).to_bytes(4, BYTE_ORDER)[4-CHECKSUM_LEN:]

    def set_checksum_flag(self, value: bool):
        self._set_flg(gzip.FHCRC, value)

    def _set_flg(self, flag: int, value: bool):
        if value:
            self.flg |= flag
        else:
            self.flg &= ~flag

    def __bytes__(self) -> bytes:
        data = bytearray(MAGIC + struct.pack(
            PARAMS_FMT,
            self.cm,
            self.flg,
            self.mtime,
            self.xfl,
            self.os,
        ))
        if self._fextra is not None:
            fextra = b''.join(bytes(f) for f in self._fextra)
            data.extend(len(fextra).to_bytes(SIZE_LEN, BYTE_ORDER) + fextra)
        if self._fname is not None:
            data.extend(self._fname.encode(ENCODING) + CSTR_ZERO)
        if self._fcomment is not None:
            data.extend(self._fcomment.encode(ENCODING) + CSTR_ZERO)
        if self.flg & gzip.FHCRC:
            data.extend(self._calc_checksum(bytes(data)))
        return bytes(data)
