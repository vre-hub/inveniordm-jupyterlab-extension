import json
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jupyter_core.paths import jupyter_data_dir

from .remote_servers import RemoteServerId

TOKEN_STORE_PATH_ENV_VAR = "INVENIORDM_JUPYTERLAB_TOKEN_STORE"

logger = logging.getLogger(__name__)


@dataclass
class StoredToken:
    access_token: str
    access_token_valid: bool
    remote_server_id: RemoteServerId
    inveniordm_user_id: str | None = None


class MultiTokenStore(ABC):
    @abstractmethod
    def get_token(self, token_id: str) -> StoredToken | None:
        pass

    @abstractmethod
    def set_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        remote_server_id: RemoteServerId,
        inveniordm_user_id: str | None = None,
    ) -> None:
        pass

    @abstractmethod
    def remove_token(self, token_id: str) -> None:
        pass


def default_token_store_path() -> Path:
    return Path(jupyter_data_dir()) / "inveniordm_jupyterlab" / "tokens.json"


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
            remote_server_id=token_data["remote_server_id"],
            inveniordm_user_id=token_data.get("inveniordm_user_id"),
        )

    def set_token(
        self,
        token_id: str,
        access_token: str,
        access_token_valid: bool,
        remote_server_id: RemoteServerId,
        inveniordm_user_id: str | None = None,
    ) -> None:
        data = self._read_tokens()
        data[token_id] = asdict(
            StoredToken(
                access_token,
                access_token_valid,
                remote_server_id,
                inveniordm_user_id,
            ),
        )
        self._write_tokens(data)

    def remove_token(self, token_id: str) -> None:
        data = self._read_tokens()
        data.pop(token_id, None)
        if data:
            self._write_tokens(data)
        else:
            self.path.unlink(missing_ok=True)

    def _read_tokens(self) -> dict[str, Any]:
        try:
            with self.path.open(encoding="utf-8") as fid:
                data: Any = json.load(fid)
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            logger.warning("Ignoring unreadable token store %s", self.path)
            return {}

        if isinstance(data, dict) and isinstance(data.get("tokens"), dict):
            return data["tokens"]

        return {}

    def _write_tokens(self, tokens: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f"{self.path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as fid:
                json.dump({"tokens": tokens}, fid)
            temporary_path.replace(self.path)
        finally:
            temporary_path.unlink(missing_ok=True)
