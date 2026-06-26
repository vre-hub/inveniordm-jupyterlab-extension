# Zenodo API Proxy: Design and Architecture

## Overview

The Zenodo API Proxy is an external service that allows a JupyterLab extension to interact with the Zenodo API without exposing long-lived Zenodo access tokens to either the browser or the Jupyter server.

The JupyterLab extension communicates exclusively with the proxy. The proxy stores the user's Zenodo access token and performs all authenticated requests to the Zenodo API on behalf of the user.

```text
JupyterLab Extension
        │
        │ HTTPS (session cookie)
        ▼
Zenodo API Proxy
        │
        │ Authorization: Bearer <Zenodo access token>
        ▼
     Zenodo API
```

The browser never receives the Zenodo access token after authentication, and the Jupyter server never stores or processes it.

## Authentication Flow

If no valid proxy session exists, the user is redirected to the Zenodo OAuth login.

The authentication flow is:

1. The JupyterLab extension opens the proxy's login endpoint.
2. The proxy starts the Zenodo OAuth authorization-code flow.
3. After successful authentication, Zenodo redirects the browser back to the proxy.
4. The proxy exchanges the authorization code for a Zenodo access token.
5. The proxy calls `GET /api/me` using the access token.
6. The returned Zenodo user id is used as the user's identity within the proxy.
7. The proxy stores the user's access token and creates a browser session.
8. The browser is redirected back to JupyterLab.

### Identity Model

The proxy uses Zenodo OAuth login as the source of user identity. After OAuth succeeds, the proxy calls Zenodo’s authenticated /api/me endpoint using the access token, and the returned Zenodo user id becomes the proxy’s internal user id.

## Stored Data

For now, the proxy stores only the information required to perform authenticated API requests.

### User record

```text
zenodo_user_id
encrypted_access_token
```

The Zenodo user id returned by `/api/me` is used as the primary key. The access token is stored encrypted.

### Session

The browser receives an opaque session cookie.

The corresponding server-side session contains only:

```text
session_id
zenodo_user_id
```

No Zenodo credentials are stored in the browser.

## API Request Flow

For every request from the JupyterLab extension:

1. The browser sends the proxy session cookie.
2. The proxy resolves the session to a Zenodo user id.
3. The proxy loads and decrypts the user's Zenodo access token.
4. The proxy performs the corresponding Zenodo API request using

```http
Authorization: Bearer <access_token>
```

5. The proxy returns the Zenodo response to the JupyterLab extension.

The access token is never returned to the client.

## Logout

Logging out deletes the proxy session.

The stored Zenodo access token remains associated with the Zenodo user id, allowing the user to authenticate again through Zenodo OAuth without creating duplicate records.

If the user wishes to revoke the connection entirely, the stored access token can simply be deleted.

## Security Properties

The Zenodo access token exists only inside the proxy.

It is never stored:

* in the JupyterLab frontend,
* in the Jupyter server,
* in browser-accessible storage.

The browser stores only an opaque session cookie, while all authenticated communication with Zenodo is performed by the proxy.
