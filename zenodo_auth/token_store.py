import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jupyter_core.paths import jupyter_data_dir

TOKEN_STORE_PATH_ENV_VAR = "ZENODO_JUPYTERLAB_TOKEN_STORE"


@dataclass
class StoredToken:
    access_token: str
    access_token_valid: bool
    sandbox: bool = False


class MultiTokenStore(ABC):
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
    def remove_access_token(self, token_id: str) -> None:
        pass


class BoundedTokenStore:
    def __init__(self, multi_store: MultiTokenStore, token_id: str = "user"):
        self.multi_store = multi_store
        self.token_id = token_id

    def get_token(self) -> StoredToken | None:
        return self.multi_store.get_token(self.token_id)

    def get_access_token(self) -> str | None:
        token = self.get_token()
        return token.access_token if token is not None else None

    def set_access_token(
        self,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        self.multi_store.set_access_token(
            self.token_id,
            access_token,
            access_token_valid,
            sandbox,
        )

    def remove_access_token(self) -> None:
        self.multi_store.remove_access_token(self.token_id)


def default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


class FileTokenStore(MultiTokenStore):
    def __init__(self, path: str | Path | None = None):
        self.path = Path(
            path
            or os.environ.get(TOKEN_STORE_PATH_ENV_VAR)
            or default_token_store_path()
        )

    def get_token(self, token_id: str) -> StoredToken | None:
        data = self._read_tokens()
        token_data = data.get(token_id)
        if not isinstance(token_data, dict) or not isinstance(
            token_data.get("access_token"),
            str,
        ):
            return None

        return StoredToken(
            access_token=token_data["access_token"],
            access_token_valid=bool(token_data.get("access_token_valid", True)),
            sandbox=bool(token_data.get("sandbox", False)),
        )

    def set_access_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        data = self._read_tokens()
        data[token_id] = asdict(
            StoredToken(access_token, access_token_valid, sandbox),
        )
        self._write_tokens(data)

    def remove_access_token(self, token_id: str) -> None:
        data = self._read_tokens()
        data.pop(token_id, None)
        if data:
            self._write_tokens(data)
        else:
            self.path.unlink(missing_ok=True)

    def _read_tokens(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}

        with self.path.open(encoding="utf-8") as fid:
            data: Any = json.load(fid)

        if isinstance(data, dict) and isinstance(data.get("tokens"), dict):
            return data["tokens"]

        # Backwards compatibility for the former single-token file format.
        if isinstance(data, dict) and isinstance(data.get("access_token"), str):
            return {"user": data}

        return {}

    def _write_tokens(self, tokens: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fid:
            json.dump({"tokens": tokens}, fid)
