import pytest

from ..vault import ImageVault


class TestImageVault:
    @pytest.mark.parametrize(
        "python_obj", (1, "foo", [1], {"foo": [1, 2, "baz", ["chaz"]]})
    )
    def test_encoding(self, python_obj):
        assert python_obj == ImageVault._from_bytes(ImageVault._to_bytes(python_obj))
