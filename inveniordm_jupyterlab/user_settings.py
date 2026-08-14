import json
from abc import ABC
from pathlib import Path

from jupyter_core.paths import jupyter_data_dir


class InvenioRDMUserSettings(ABC):
    """Define storage and validation for extension user settings."""
    def __init__(self, jupyterlab_root_dir: Path):
        """Initialize settings relative to the JupyterLab root."""
        self.jupyterlab_root_dir = jupyterlab_root_dir

    def get_default_downloads_directory(self) -> Path:
        """
        Get the default directory where InvenioRDM downloads are stored.
        """
        return self.jupyterlab_root_dir / "inveniordm_downloads"

    def get_downloads_directory(self) -> Path:
        """
        Get the directory where InvenioRDM downloads are stored.
        """
        downloads_dir = self._get_downloads_directory()
        if downloads_dir is None:
            return self.get_default_downloads_directory()
        return downloads_dir

    def _get_downloads_directory(self) -> Path | None:
        """
        Get the directory where InvenioRDM downloads are stored.
        """
        ...

    def set_downloads_directory(self, path: str):
        """
        Set the directory where InvenioRDM downloads should be stored.
        Creates the directory if it does not exist.
        Validates that the path is a directory and is writable.
        """
        if not Path(path).exists():
            Path(path).mkdir(parents=True, exist_ok=True)
        if not Path(path).is_dir():
            raise ValueError(f"Path {path} is not a directory.")
        self._set_downloads_directory(str(self.jupyterlab_root_dir / path))

    def _set_downloads_directory(self, path: str):
        """
        Set the directory where InvenioRDM downloads should be stored.
        """
        ...

    def unset_downloads_directory(self):
        """
        Unset the configured downloads directory.
        """
        self._unset_downloads_directory()

    def _unset_downloads_directory(self):
        """
        Unset the configured downloads directory.
        """
        ...


class InvenioRDMUserSettingsFromFile(InvenioRDMUserSettings):
    """
    Store InvenioRDM user settings in a file.
    """

    def __init__(self, jupyterlab_root_dir: Path):
        """Load file-backed settings for the JupyterLab root."""
        super().__init__(jupyterlab_root_dir)
        self.settings_file = Path(jupyter_data_dir()) / "inveniordm_user_settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        """Load settings from disk, returning defaults when absent."""
        if self.settings_file.exists():
            with open(self.settings_file, "r") as f:
                return json.load(f)
        return {}

    def _save_settings(self):
        """Persist the current settings to disk."""
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f)

    def _get_downloads_directory(self) -> Path | None:
        """Return the configured download directory, if any."""
        downloads_dir = self.settings.get("downloads_dir")
        if downloads_dir is None or downloads_dir.strip() == "":
            return None
        return Path(downloads_dir)

    def _set_downloads_directory(self, path: str):
        """Persist a configured download directory."""
        self.settings["downloads_dir"] = path
        self._save_settings()

    def _unset_downloads_directory(self):
        """Remove the persisted download-directory override."""
        self.settings.pop("downloads_dir", None)
        self._save_settings()
