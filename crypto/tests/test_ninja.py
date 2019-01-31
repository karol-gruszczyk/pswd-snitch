import os

import pytest

from PIL import Image

from ..ninja import BytesNinja, ImageNinja, EncryptedBytesNinja, EncryptedImageNinja


class TestBytesNinja:
    def test_get_bits(self):
        assert [1] * 4 + [0] * 4 == list(BytesNinja._get_bits(b"\xf0"))

    def test_get_bytes(self):
        assert b"\xf0" == BytesNinja._get_bytes([1] * 4 + [0] * 4)

    @pytest.mark.parametrize(
        "byte, bit, expected",
        (
            (0xFF, False, 0xFE),
            (0xFF, True, 0xFF),
            (0x00, True, 0x01),
            (0x00, False, 0x00),
        ),
    )
    def test_set_last_bit(self, byte, bit, expected):
        assert expected == BytesNinja._set_last_bit(byte, bit)

    def test_hide_message(self):
        data_ninja = BytesNinja(bytes(16))
        data_ninja.hide_message(bytes([0b11010110]))
        assert b"\x01\x01\x00\x01\x00\x01\x01\x00" + b"\x01" * 8 == data_ninja.data

    def test_read_message(self):
        data_ninja = BytesNinja(b"\x01\x01\x00\x01\x00\x01\x01\x00" + b"\x01" * 8)
        assert bytes([0b11010110]) == data_ninja.read_message()

    @pytest.mark.parametrize("data", [b"foo"])
    def test_integration(self, data):
        data_ninja = BytesNinja(bytes(100))
        data_ninja.hide_message(data)

        assert data == data_ninja.read_message()


class TestImageMixin:
    @classmethod
    def setup_class(cls):
        image = Image.new("RGB", (100, 100), color="black")
        image.save("test.png")
        image.close()

    @classmethod
    def teardown_class(cls):
        os.remove("test.png")


class TestImageNinja(TestImageMixin):
    @pytest.mark.parametrize("message", (b"f", b"{--21-37--}", b"foo"))
    def test_encryption(self, message):
        crypto_image = ImageNinja("test.png")
        crypto_image.hide_message(message)
        crypto_image.save("test_out.png")

        assert message == ImageNinja("test_out.png").read_message()
        os.remove("test_out.png")


class TestEncryptedBytesNinja:
    def test_invalid_password(self):
        ninja = EncryptedBytesNinja(bytes(3000), password="foo")
        ninja.hide_message(b"secret")

        ninja = EncryptedBytesNinja(ninja.data, password="baz")
        with pytest.raises(EncryptedBytesNinja.InvalidPassword):
            ninja.read_message()

    @pytest.mark.parametrize("message", (b"f", b"{--21-37--}", b"foo"))
    def test_encryption(self, message):
        ninja = EncryptedBytesNinja(bytes(3000), password="foo")
        ninja.hide_message(message)

        ninja = EncryptedBytesNinja(ninja.data, password="foo")
        assert message == ninja.read_message()


class TestEncryptedImageNinja(TestImageMixin):
    def test_invalid_password(self):
        ninja = EncryptedImageNinja("test.png", password="foo")
        ninja.hide_message(b"secret")
        ninja.save("test_out.png")

        ninja = EncryptedImageNinja("test_out.png", password="baz")
        with pytest.raises(EncryptedImageNinja.InvalidPassword):
            ninja.read_message()

        os.remove("test_out.png")

    @pytest.mark.parametrize("message", (b"f", b"{--21-37--}", b"foo"))
    def test_encryption(self, message):
        ninja = EncryptedImageNinja("test.png", password="foo")
        ninja.hide_message(message)
        ninja.save("test_out.png")

        ninja = EncryptedImageNinja("test_out.png", password="foo")
        assert message == ninja.read_message()

        os.remove("test_out.png")
