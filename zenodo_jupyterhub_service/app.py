import os

from jupyterhub.services.auth import HubAuth, HubAuthenticated
from tornado import ioloop, web


hub_auth = HubAuth.instance()


class WhoAmIHandler(HubAuthenticated, web.RequestHandler): # type: ignore[reportIncompatibleMethodOverride]
    def initialize(self, hub_auth):
        self.hub_auth = hub_auth

    @web.authenticated
    def get(self):
        self.write({"name": self.current_user["name"]})


prefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"].rstrip("/")
app = web.Application(
    [
        (prefix + r"/(?:whoami)?/?", WhoAmIHandler, {"hub_auth": hub_auth}),
    ]
)
app.listen(10101, "127.0.0.1")
ioloop.IOLoop.current().start()
