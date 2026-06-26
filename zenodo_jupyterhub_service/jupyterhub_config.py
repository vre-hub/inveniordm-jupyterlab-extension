"""
This is a JupyterHub configuration file for
- development purposes
- showing how to configure the Zenodo JupyterHub service to work with JupyterHub
"""

import os

from traitlets.config.application import get_config


c = get_config()
here = os.path.dirname(__file__)
root = os.path.dirname(here)

c.JupyterHub.bind_url = "http://127.0.0.1:8000"
c.ConfigurableHTTPProxy.api_url = "http://127.0.0.1:8002"
c.JupyterHub.cookie_secret_file = os.path.join(here, "jupyterhub_cookie_secret")
c.JupyterHub.db_url = f"sqlite:///{os.path.join(here, 'jupyterhub.sqlite')}"

c.JupyterHub.authenticator_class = "dummy"
c.DummyAuthenticator.allow_all = True
c.DummyAuthenticator.password = "jupyter"

c.JupyterHub.spawner_class = "simple" # "dummy"
c.Spawner.default_url = "/lab"
c.Spawner.notebook_dir = os.path.join(root, "lab_cwd")

"""
The following configuration is for the Zenodo JupyterHub service.
When configuring a real JupyterHub deployment,
include the following settings to connect the service properly to the JupyterHub instance.
"""

# Define the scopes of the JUPYTERHUB_API_TOKEN (used in python extensions)
c.Spawner.server_token_scopes = [
    "access:services!service=zenodo-jupyterhub-service",
]

c.JupyterHub.load_roles = [
    {
        # allow users to access the Zenodo JupyterHub service
        "name": "user",
        "scopes": ["self", "access:services!service=zenodo-jupyterhub-service"],
    }
]

c.JupyterHub.services = [
    {
        "name": "zenodo-jupyterhub-service",
        "url": "http://127.0.0.1:10101",
        "api_token": os.environ["ZENODO_JUPYTERHUB_SERVICE_API_TOKEN"],
    }
]
