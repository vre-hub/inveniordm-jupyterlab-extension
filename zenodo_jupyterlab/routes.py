import json

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

class HelloRouteHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": (
                "Hello, world!"
                " This is the '/zenodo-jupyterlab/hello' endpoint."
                " Try visiting me in your browser!"
            ),
        }))

class PutZenodoAccessTokenHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def put(self):
        data = self.get_json_body()
        access_token = data.get("access_token")
        if not access_token:
            self.set_status(400)
            self.finish(json.dumps({"error": "Missing 'access_token' in request body"}))
            return

        user_name = self.current_user.username # should be secure and stable if not renamed or remapped
        print(f"Received access token from user: {user_name} , access_token: {access_token}")

        # TODO properly store access token somewhere

        self.finish(json.dumps({"message": "Access token received successfully"}))


def setup_route_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    zenodo_base_url = url_path_join(base_url, "zenodo-jupyterlab")
    handlers = [
        (url_path_join(zenodo_base_url, "hello"), HelloRouteHandler),
        (url_path_join(zenodo_base_url, "access-token"), PutZenodoAccessTokenHandler),
    ]

    web_app.add_handlers(host_pattern, handlers)
