import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class TokenStore(ABC):
    """Store access tokens by stable identifier."""

    @abstractmethod
    def get_access_token(self, token_id: str) -> str | None:
        pass

    @abstractmethod
    def set_access_token(self, token_id: str, access_token: str) -> None:
        pass

    @abstractmethod
    def remove_access_token(self, token_id: str) -> None:
        pass

    def has_access_token(self, token_id: str) -> bool:
        return self.get_access_token(token_id) is not None


class FileTokenStore(TokenStore):
    """
    Persist access tokens as a JSON mapping on disk.
    This is NOT secure for multiple users, because the file is readable by any user on the system,
    even from jupyter notebooks.
    If multiple users use the same Jupyter server, they will ALL be able to read the file.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get_access_token(self, token_id: str) -> str | None:
        return self._read_tokens().get(token_id)

    def set_access_token(self, token_id: str, access_token: str) -> None:
        tokens = self._read_tokens()
        tokens[token_id] = access_token
        self._write_tokens(tokens)

    def remove_access_token(self, token_id: str) -> None:
        tokens = self._read_tokens()
        tokens.pop(token_id, None)
        self._write_tokens(tokens)

    def _read_tokens(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        with self.path.open(encoding="utf-8") as fid:
            data: Any = json.load(fid)

        if not isinstance(data, dict):
            return {}

        return {
            str(token_id): token
            for token_id, token in data.items()
            if isinstance(token, str)
        }

    def _write_tokens(self, tokens: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")

        with tmp_path.open("w", encoding="utf-8") as fid:
            json.dump(tokens, fid)

        os.replace(tmp_path, self.path)
