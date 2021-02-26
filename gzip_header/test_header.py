import copy
import gzip
import io
import unittest

from .header import (
    MAGIC,
    Field,
    Header,
)


class HeaderTestCase(unittest.TestCase):

    def test_header(self):
        buf = io.BytesIO()
        with gzip.GzipFile('test_filename', 'wb', fileobj=buf) as f:
            f.write(b'test data')
        buf.seek(0)
        h = Header.from_reader(buf)
        h_origin = copy.deepcopy(h)
        h.fcomment = 'hello'
        self.assertNotEqual(bytes(h_origin), bytes(h))
        h.fcomment = None
        self.assertEqual(bytes(h_origin), bytes(h))
        h.set_checksum_flag(True)
        data = bytes(h)
        h1 = Header.from_reader(io.BytesIO(data))
        self.assertEqual(data, bytes(h1))
        self.assertEqual(h, h1)
        h.fextra = [Field(MAGIC, b'extra data')]
        data = bytes(h)
        h1 = Header.from_reader(io.BytesIO(data))
        self.assertEqual(data, bytes(h1))
        self.assertEqual(h, h1)
        h.fextra = None
        h.set_checksum_flag(False)
        self.assertEqual(bytes(h_origin), bytes(h))
