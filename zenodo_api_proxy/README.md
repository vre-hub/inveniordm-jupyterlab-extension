# Zenodo API Proxy

Proxy for the Zenodo API that requires login via OAuth and can execute requests on behalf of the user.

## Development Setup

Use this for the developer application registration on the Zenodo Instance.

### Zenodo Sandbox OAuth Application Form for local development

| Field | Value |
| --- | --- |
| Name | `Zenodo JupyterLab Proxy Local Dev` |
| Description | `Local development OAuth application for testing the Zenodo JupyterLab API proxy against Zenodo Sandbox.` |
| Website URL | `http://127.0.0.1:8001` |
| Redirect URIs | `http://127.0.0.1:8001/auth/callback` |
| Client type | `Confidential` |

### Running the Proxy

Copy the generated client credentials into your shell before starting the proxy:

```bash
export ZENODO_CLIENT_ID="..."
export ZENODO_CLIENT_SECRET="..."
python -m zenodo_api_proxy
```

Then start login in the browser:

```text
http://127.0.0.1:8001/auth/login?return_to=http%3A%2F%2Flocalhost%3A8888%2Flab
```

Check whether the proxy session exists:

```text
http://127.0.0.1:8001/auth/status
```

### Notes

- The redirect URI in Zenodo must exactly match `PROXY_PUBLIC_URL + /auth/callback`.

### Available routes:

GET /health
GET /auth/login
GET /auth/callback
GET /auth/status
GET /auth/logout

Authenticated Zenodo API proxy routes mirror Zenodo's own `/api/...` paths:

GET /api/...
POST /api/...
PUT /api/...
PATCH /api/...
DELETE /api/...

These routes require the `zenodo_proxy_session` cookie. The proxy adds the
stored Zenodo OAuth access token server-side and forwards the request to the
configured Zenodo instance.
