from dataclasses import dataclass
import json
import typing as t

from .ninja import EncryptedImageNinja


@dataclass()
class Password:
    name: str
    login: str
    passphrase: str

    def __str__(self) -> str:
        return f"{self.name}({self.login})"


class ImageVault:
    passwords: t.List[Password]

    def __init__(self, path: str, password: str, for_write=False):
        self.path = path
        self.image_ninja = EncryptedImageNinja(self.path, password=password)
        self.passwords = []
        if not for_write:
            self.passwords = self._from_bytes(self.image_ninja.read_message())

    @classmethod
    def _to_bytes(cls, passwords: t.List[Password]) -> bytes:
        assert isinstance(passwords, list) and all(
            isinstance(p, Password) for p in passwords
        ), f"Expected `{repr(passwords)}` to be of type List[Password]"
        data = [[p.name, p.login, p.passphrase] for p in passwords]
        return json.dumps(data).encode()

    @classmethod
    def _from_bytes(cls, data: bytes) -> t.List[Password]:
        data = json.loads(data.decode())
        assert isinstance(data, list) and all(
            isinstance(p, list) and len(p) == 3 for p in data
        ), f"Expected `{repr(data)}` to be of type List[List[3]]"
        return [Password(*p) for p in data]

    def save(self, path: str = None):
        self.image_ninja.hide_message(self._to_bytes(self.passwords))
        self.image_ninja.save(path or self.path)


123
