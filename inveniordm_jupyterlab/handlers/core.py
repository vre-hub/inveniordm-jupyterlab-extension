import json

import requests
import tornado

from inveniordm_auth.remote_servers import RemoteServerRegistry

from ..inveniordm_auth.auth_controller import InvenioRDMAuthController
from ..inveniordm_requests.inveniordm_requests_factory import (
    InvenioRDMRequestsFactory,
)
from ..util.sse import EventBus, stream_user_events
from .base import APIHandler, GetInvenioRDMRequests, get_user_id


class HelloRouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                {
                    "data": (
                        "Hello, world!"
                        " This is the '/inveniordm-jupyterlab/hello' endpoint."
                        " Try visiting me in your browser!"
                    ),
                }
            )
        )


class InvenioRDMAccessTokenHandler(APIHandler):
    def initialize(
        self,
        inveniordm_requests_factory: InvenioRDMRequestsFactory,
    ):
        self.inveniordm_requests_factory = inveniordm_requests_factory

    @tornado.web.authenticated
    def get(self):
        status = self.inveniordm_requests_factory.get_access_token_status(self)
        self.finish(json.dumps(status.__dict__))


class InvenioRDMRemoteServersHandler(APIHandler):
    def initialize(self, remote_servers: RemoteServerRegistry, request_mode: str):
        self.remote_servers = remote_servers
        self.request_mode = request_mode

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                [
                    {
                        "id": server.id,
                        "label": server.label,
                        "login_available": (
                            self.request_mode == "proxy"
                            or server.oauth_client_id is not None
                        ),
                    }
                    for server in self.remote_servers.all()
                ]
            )
        )


class InvenioRDMRemoteServersDefaultHandler(APIHandler):
    def initialize(self, remote_servers: RemoteServerRegistry, request_mode: str):
        self.remote_servers = remote_servers
        self.request_mode = request_mode

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps(
                {
                    "id": self.remote_servers.default.id,
                    "label": self.remote_servers.default.label,
                    "login_available": (
                        self.request_mode == "proxy"
                        or self.remote_servers.default.oauth_client_id is not None
                    ),
                }
            )
        )


class InvenioRDMCurrentRemoteServerHandler(APIHandler):
    def initialize(
        self,
        inveniordm_requests_factory: InvenioRDMRequestsFactory,
    ):
        self.inveniordm_requests_factory = inveniordm_requests_factory

    @tornado.web.authenticated
    def get(self):
        inveniordm_requests = (
            self.inveniordm_requests_factory.create_inveniordm_requests(self)
        )
        remote_server_id = self.inveniordm_requests_factory.get_remote_server_id(
            inveniordm_requests
        )
        remote_server = self.inveniordm_requests_factory.remote_servers.get(
            remote_server_id
        )
        self.finish(
            json.dumps(
                {
                    "id": remote_server.id,
                    "display_name": remote_server.label,
                }
            )
        )


class InvenioRDMAuthHandler(APIHandler):
    def initialize(self, inveniordm_auth_controller: InvenioRDMAuthController):
        self.inveniordm_auth_controller = inveniordm_auth_controller

    @tornado.web.authenticated
    def get(self, action: str):
        if action == "login":
            self.inveniordm_auth_controller.login(self)
            return

        if action == "logout":
            self.inveniordm_auth_controller.logout(self)
            return

        if action == "callback":
            self.inveniordm_auth_controller.callback(self)
            return

        self.set_status(404)
        self.finish(json.dumps({"message": "Unknown auth action"}))


class InvenioRDMMeHandler(APIHandler):
    def initialize(self, get_inveniordm_requests: GetInvenioRDMRequests):
        self.get_inveniordm_requests = get_inveniordm_requests

    @tornado.web.authenticated
    def get(self):
        try:
            profile = self.get_inveniordm_requests(self).get_inveniordm_me()
        except ValueError as error:
            self.set_status(401)
            self.finish(json.dumps({"message": str(error)}))
            return
        except KeyError as error:
            self.set_status(502)
            self.finish(
                json.dumps({"message": f"Missing field in InvenioRDM profile: {error}"})
            )
            return
        except requests.RequestException as error:
            self.set_status(getattr(error.response, "status_code", 502))
            self.finish(json.dumps({"message": str(error)}))
            return

        self.finish(json.dumps(profile))


class InvenioRDMEventsHandler(APIHandler):
    def initialize(
        self,
        event_bus: EventBus,
    ):
        self.event_bus = event_bus

    @tornado.web.authenticated
    async def get(self):
        """
        Allow clients to subscribe to all SSE events for the current user.
        The connection will be kept open and events will be sent as they occur.
        """
        await stream_user_events(
            self,
            event_bus=self.event_bus,
            user_id=get_user_id(self),
        )
