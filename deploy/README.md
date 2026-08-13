# Deploying the InvenioRDM API proxy

The JupyterLab extension can run in two request modes.

**`local`** (the default) talks to InvenioRDM straight from the user's Jupyter
server. The OAuth redirect URI is built per request as
`<public-url><base_url>/inveniordm-jupyterlab/auth/callback`. On a single-user
JupyterLab that resolves to `http://localhost:8888/inveniordm-jupyterlab/auth/callback`,
which the bundled client IDs are registered for.

**`proxy`** routes API calls and the OAuth flow through a separate service, so
the access token never reaches the user's server.

## Why multi-user deployments need `proxy`

Under JupyterHub, `base_url` is `/user/<username>/`, so in `local` mode every
user gets a *different* redirect URI:

```
https://jupyter.example.org/user/alice/inveniordm-jupyterlab/auth/callback
https://jupyter.example.org/user/bob/inveniordm-jupyterlab/auth/callback
```

InvenioRDM matches redirect URIs as exact strings with no wildcard support, so
a single OAuth application cannot cover them — you would need one registered
application per user. `INVENIORDM_JUPYTERLAB_PUBLIC_URL` overrides only the
scheme and host, not the `base_url` segment, so it does not help.

The proxy has one fixed redirect URI, `<PROXY_PUBLIC_URL>/auth/callback`,
shared by every user. It can also be a *confidential* OAuth client, since
`INVENIORDM_CLIENT_SECRET` lives in the proxy rather than in user pods.

## Contents

- `docker/Dockerfile` — image running `python -m inveniordm_api_proxy`. It
  installs only `inveniordm_api_proxy` and `inveniordm_auth`, so no node/yarn
  build is needed.
- `helm/inveniordm-api-proxy/` — Helm chart for one proxy instance.

## One release per InvenioRDM instance

The proxy reads a single `INVENIORDM_BASE_URL` and a single client ID from its
environment; it does not multiplex. Its own README puts it as: *"Each proxy
deployment supplies these values independently; it does not read the JupyterLab
extension's remote-server configuration."*

Serving Zenodo, CDS and Zenodo Sandbox therefore means **three releases**, each
with its own hostname, OAuth application, and `sessionCookieName`. Sharing a
cookie name between releases breaks logins — the OAuth state cookie is derived
from it as `<name>_oauth_state`.

See `helm/inveniordm-api-proxy/values-example.yaml` for a worked setup.

## Deployment notes

**State.** The proxy stores tokens with `FileTokenStore`, a single JSON file
with no cross-process locking. The chart is therefore single-replica with
`strategy: Recreate`, and the PVC carries `helm.sh/resource-policy: keep`. That
volume holds live InvenioRDM access tokens — per the project's own notes those
last up to a year — so treat it as secret-grade storage.

**Defaults that must be overridden.** The proxy ships localhost-oriented
defaults that are wrong in a cluster:

| Setting | Upstream default | Chart handling |
| --- | --- | --- |
| `PROXY_HOST` | `127.0.0.1` | forced to `0.0.0.0` |
| `PROXY_ALLOWED_CORS_ORIGINS` | `localhost:8888` | `proxy.allowedCorsOrigins`, warns if empty |
| `PROXY_ALLOWED_RETURN_HOSTS` | `localhost`, `127.0.0.1` | `proxy.allowedReturnHosts`, warns if empty |
| `INVENIORDM_JUPYTERLAB_TOKEN_STORE` | under `jupyter_data_dir()` | set to the mounted volume |

**Cookies.** The session cookie is `SameSite=Lax`. Host the proxy under the
same registrable domain as JupyterHub (e.g. both under `example.org`) so the
login redirect keeps its cookie.

**Redirect URI.** Must match `<publicUrl>/auth/callback` exactly in the
registered OAuth application. `helm install` prints the value to use.

## Wiring up the extension

Once the proxies are up, configure the singleuser servers:

```python
c.InvenioRDMJupyterLab.request_mode = "proxy"
c.InvenioRDMJupyterLab.remote_servers = {
    "zenodo": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "<client id>",
        "proxy_url": "https://inveniordm-proxy-zenodo.example.org",
        "proxy_session_cookie_name": "zenodo_proxy_session",
    },
}
```

`proxy_url` and `proxy_session_cookie_name` are both required in proxy mode;
`validate_proxy_configuration()` rejects empty values at server start.
