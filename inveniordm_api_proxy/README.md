# InvenioRDM API Proxy

Proxy for the InvenioRDM API that requires login via OAuth and can execute requests on behalf of the user.

## Development Setup

Use this for the developer application registration on the InvenioRDM Instance.

### InvenioRDM Sandbox OAuth Application Form for local development

| Field         | Value                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------- |
| Name          | `InvenioRDM JupyterLab Proxy Local Dev`                                                                           |
| Description   | `Local development OAuth application for testing the InvenioRDM JupyterLab API proxy against InvenioRDM Sandbox.` |
| Website URL   | `http://127.0.0.1:8001`                                                                                           |
| Redirect URIs | `http://127.0.0.1:8001/auth/callback`                                                                             |
| Client type   | `Confidential`                                                                                                    |

### Running the Proxy

Copy the generated client credentials into your shell before starting the proxy:

```bash
export INVENIORDM_BASE_URL="https://zenodo.org"
export INVENIORDM_CLIENT_ID="HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt"
export PROXY_HOST="127.0.0.1"
export PROXY_PUBLIC_URL="http://127.0.0.1:8003"
export PROXY_PORT="8003"
export INVENIORDM_PROXY_SESSION_COOKIE_NAME="zenodo_production_proxy_session"
python -m inveniordm_api_proxy
```

For just running the proxy with default credentials, run

```bash
unset INVENIORDM_BASE_URL
unset INVENIORDM_CLIENT_ID # or set the client ID yourself
unset PROXY_HOST
unset PROXY_PUBLIC_URL
unset PROXY_PORT
unset INVENIORDM_PROXY_SESSION_COOKIE_NAME
python -m inveniordm_api_proxy
```

Each proxy deployment supplies these values independently; it does not read the
JupyterLab extension's remote-server configuration. The proxy defaults to the
InvenioRDM sandbox; set `INVENIORDM_BASE_URL` and `INVENIORDM_PROXY_SESSION_COOKIE_NAME` to
target another server.

Then start login in the browser:

```text
http://127.0.0.1:8001/auth/login?return_to=http%3A%2F%2Flocalhost%3A8888%2Flab
```

Check whether the proxy session exists:

```text
http://127.0.0.1:8001/auth/status
```

To use the proxy, you need to configure the JupyterLab extension to point to the proxy URL and session cookie name, e.g. like this:

```python
c.InvenioRDMJupyterLab.remote_servers = {
    "zenodo": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
        "proxy_url": "http://127.0.0.1:8003/",
        "proxy_session_cookie_name": "zenodo_production_proxy_session",
    },
    "zenodo_sandbox": {
        "label": "Zenodo Sandbox",
        "base_url": "https://sandbox.zenodo.org",
        "proxy_url": "http://127.0.0.1:8001/",
        "proxy_session_cookie_name": "zenodo_sandbox_proxy_session",
    },
}
```

### Notes

- The redirect URI in InvenioRDM must exactly match `PROXY_PUBLIC_URL + /auth/callback`.
- Use a different `INVENIORDM_PROXY_SESSION_COOKIE_NAME` for each local proxy
  instance. The OAuth state cookie name is derived from it as
  `<session-cookie-name>_oauth_state`.

### Available routes:

GET /health
GET /auth/login
GET /auth/callback
GET /auth/status
GET /auth/logout

Authenticated InvenioRDM API proxy routes mirror InvenioRDM's own `/api/...` paths:

GET /api/...
POST /api/...
PUT /api/...
PATCH /api/...
DELETE /api/...

These routes require the configured proxy session cookie. The proxy adds the
stored InvenioRDM OAuth access token server-side and forwards the request to the
configured InvenioRDM instance.
