from typing import Protocol

from jupyter_server.base.handlers import APIHandler


class InvenioRDMAuthController(Protocol):
    def login(self, handler: APIHandler) -> None:
        pass

    def logout(self, handler: APIHandler) -> None:
        pass

    def callback(self, handler: APIHandler) -> None:
        pass
