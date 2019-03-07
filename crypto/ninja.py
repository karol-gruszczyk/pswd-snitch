import base64
import functools
import typing as t

from PIL import Image

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from more_itertools import grouper


class BytesNinja:
    EOT = b"\xff"
    EOT_FILLER = b"\x00"

    def __init__(self, data: bytes):
        self.data = data

    @staticmethod
    def _get_bits(data: bytes) -> t.Iterable[int]:
        for byte in data:
            yield from (byte >> i & 0x01 for i in range(7, -1, -1))

    @staticmethod
    def _get_bytes(bits: t.Iterable[int]) -> bytes:
        return bytes(
            functools.reduce(lambda v, b: v << 1 | b, byte_tuple, 0)
            for byte_tuple in grouper(8, bits)
            if None not in byte_tuple
        )

    @staticmethod
    def _get_last_bits(data: bytes) -> t.Iterator[bool]:
        yield from (byte & 0x01 for byte in data)

    @staticmethod
    def _set_last_bit(byte: int, bit: bool) -> int:
        byte &= ~1
        if bit:
            byte |= 1
        return byte

    @classmethod
    def fill_bits(cls, bits):
        yield from bits
        yield from cls._get_bits(cls.EOT)  # FIXME: there must be a better EOT
        while True:
            yield from cls._get_bits(cls.EOT_FILLER)

    def hide_message(self, message: bytes):
        assert len(message) * 8 + 1 <= len(self.data)
        bits = self.fill_bits(self._get_bits(message))
        self.data = bytes(self._set_last_bit(byte, next(bits)) for byte in self.data)

    def read_message(self) -> bytes:
        bits = self._get_last_bits(self.data)
        data = self._get_bytes(bits)
        try:
            return data[: data.rindex(self.EOT)]
        except ValueError:
            raise


class ImageNinjaMixin:
    def __init__(self, path: str):
        assert not path.lower().endswith(".jpg"), f"Compression not supported"
        image = Image.open(path)
        self.size = image.size
        self.mode = image.mode
        super().__init__(image.tobytes())
        image.close()

    def save(self: t.Union["ImageNinjaMixin", BytesNinja], path: str):
        image = Image.frombytes(self.mode, self.size, self.data)
        image.save(path)
        image.close()


class ImageNinja(ImageNinjaMixin, BytesNinja):
    pass


class EncryptionMixin:
    SALT = b"\xe0\x92\xa1&\xf7>\r\x94sa\xea9\xcf\x8dO\x0f"  # FIXME: is this safe?

    class InvalidPassword(Exception):
        pass

    def __init__(self, *args, password: str):
        super().__init__(*args)
        self.fernet = Fernet(self._get_key(password))

    @classmethod
    def _get_key(cls, password: str):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=cls.SALT,
            iterations=100_000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def hide_message(self, message: bytes):
        super().hide_message(self.fernet.encrypt(message))

    def read_message(self):
        try:
            return self.fernet.decrypt(super().read_message())
        except (InvalidToken, ValueError):
            raise self.InvalidPassword()


class EncryptedBytesNinja(EncryptionMixin, BytesNinja):
    pass


class EncryptedImageNinja(EncryptionMixin, ImageNinja):
    pass
