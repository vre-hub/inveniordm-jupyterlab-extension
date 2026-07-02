from __future__ import annotations

from .base_handler import BaseProxyHandler


class StatusHandler(BaseProxyHandler):
    def get(self) -> None:
        zenodo_user_id = self.current_zenodo_user_id()
        if zenodo_user_id is None:
            self.write_json({"authenticated": False})
            return

        self.write_json(
            {
                "authenticated": True,
                "zenodo_base_url": self.config.zenodo_base_url,
                "zenodo_user_id": zenodo_user_id,
            }
        )
