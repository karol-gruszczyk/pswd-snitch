import os

import pytest

from PIL import Image

from ..vault import ImageVault, Password


class TestImageVault:
    @pytest.mark.parametrize(
        "passwords", ([], [Password('foo', 'bar', 'baz')])
    )
    def test_encoding(self, passwords):
        assert passwords == ImageVault._from_bytes(ImageVault._to_bytes(passwords))

    def test_performance(self):
        image = Image.new('RGB', (4000, 4000), color='black')
        image.save('test.png')

        vault = ImageVault('test.png', password='', for_write=True)
        vault.save('test.png')

        os.remove('test.png')
