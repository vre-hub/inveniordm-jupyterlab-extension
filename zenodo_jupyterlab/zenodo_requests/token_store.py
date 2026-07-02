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


class TokenStore(ABC):
    @abstractmethod
    def get_token(self) -> StoredToken | None:
        pass

    def get_access_token(self) -> str | None:
        token = self.get_token()
        return token.access_token if token is not None else None

    @abstractmethod
    def set_access_token(
        self,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        pass

    @abstractmethod
    def remove_access_token(self) -> None:
        pass


def default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "zenodo_jupyterlab" / "tokens.json"


class FileTokenStore(TokenStore):
    def __init__(self, path: str | Path | None = None):
        self.path = Path(
            path
            or os.environ.get(TOKEN_STORE_PATH_ENV_VAR)
            or default_token_store_path()
        )

    def get_token(self) -> StoredToken | None:
        if not self.path.exists():
            return None

        with self.path.open(encoding="utf-8") as fid:
            data: Any = json.load(fid)

        if not isinstance(data, dict) or not isinstance(data.get("access_token"), str):
            return None

        return StoredToken(
            access_token=data["access_token"],
            access_token_valid=bool(data.get("access_token_valid", True)),
            sandbox=bool(data.get("sandbox", False)),
        )

    def set_access_token(
        self,
        access_token: str,
        access_token_valid: bool,
        sandbox: bool = False,
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fid:
            json.dump(
                asdict(StoredToken(access_token, access_token_valid, sandbox)),
                fid,
            )

    def remove_access_token(self) -> None:
        self.path.unlink(missing_ok=True)
