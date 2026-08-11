from __future__ import annotations

from .base_handler import BaseProxyHandler


class StatusHandler(BaseProxyHandler):
    def get(self) -> None:
        inveniordm_user_id = self.current_inveniordm_user_id()
        if inveniordm_user_id is None:
            self.write_json({"authenticated": False})
            return

        self.write_json(
            {
                "authenticated": True,
                "inveniordm_base_url": self.config.inveniordm_base_url,
                "inveniordm_user_id": inveniordm_user_id,
            }
        )
