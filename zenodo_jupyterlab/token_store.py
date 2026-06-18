import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


@dataclass
class StoredToken:
    access_token: str
    access_token_valid: bool
    sandbox: bool = False


class TokenStore(ABC):
    """Store access tokens by stable identifier."""

    @abstractmethod
    def get_token(self, token_id: str) -> StoredToken | None:
        pass

    def get_access_token(self, token_id: str) -> str | None:
        token = self.get_token(token_id)
        return token.access_token if token is not None else None

    @abstractmethod
    def set_access_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        pass

    @abstractmethod
    def set_access_token_validity(
        self, token_id: str, access_token_valid: bool
    ) -> None:
        """
        Update the validity of the access token without changing the token itself.
        Call this after making a call to Zenodo with the token
        to update the validity based on whether the call succeeded or failed due to auth.
        """
        pass

    @abstractmethod
    def remove_access_token(self, token_id: str) -> None:
        pass



class FileTokenStore(TokenStore):
    """
    Persist access tokens as a JSON mapping on disk.
    This is NOT secure for multiple users, because the file is readable by any user on the system,
    even from jupyter notebooks.
    If multiple users use the same Jupyter server, they will ALL be able to read the file.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get_token(self, token_id: str) -> StoredToken | None:
        return self._read_tokens().get(token_id)

    def set_access_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        tokens = self._read_tokens()
        tokens[token_id] = StoredToken(access_token, access_token_valid, sandbox)
        self._write_tokens(tokens)

    def set_access_token_validity(
        self, token_id: str, access_token_valid: bool
    ) -> None:
        tokens = self._read_tokens()
        token = tokens.get(token_id)
        if token is None:
            return
        tokens[token_id] = replace(token, access_token_valid=access_token_valid)
        self._write_tokens(tokens)

    def remove_access_token(self, token_id: str) -> None:
        tokens = self._read_tokens()
        tokens.pop(token_id, None)
        self._write_tokens(tokens)

    def _read_tokens(self) -> dict[str, StoredToken]:
        if not self.path.exists():
            return {}

        with self.path.open(encoding="utf-8") as fid:
            data: Any = json.load(fid)

        if not isinstance(data, dict):
            return {}

        return {
            str(token_id): StoredToken(**token)
            for token_id, token in data.items()
            if isinstance(token, dict)
        }

    def _write_tokens(self, tokens: dict[str, StoredToken]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")

        with tmp_path.open("w", encoding="utf-8") as fid:
            json.dump(
                {token_id: asdict(token) for token_id, token in tokens.items()},
                fid,
            )

        os.replace(tmp_path, self.path)
