# Configuration

Configure the extension in a Jupyter Server configuration file, such as
`jupyter_server_config.py`:

```python
c = get_config()  # noqa: F821

c.InvenioRDMJupyterLab.remote_servers_mode = "extend"
c.InvenioRDMJupyterLab.remote_servers = {
    # Built-in fields such as label and base_url are inherited by ID.
    "zenodo": {"oauth_client_id": "my-zenodo-oauth-client-id"},
    "institutional_repository": {
        "label": "Institutional Repository",
        "base_url": "https://research.example.org",
        "oauth_client_id": "my-institutional-oauth-client-id",
    },
}
c.InvenioRDMJupyterLab.default_remote_server = "zenodo" # default
c.InvenioRDMJupyterLab.enable_builtin_local_oauth = True
```

## Quickstart

### Enabling Login for JupyterLab instances other than `http://localhost:8888`

If your JupyterLab instance is not run under `http://localhost:8888`, the built-in OAuth client IDs for Zenodo and CDS will not work. You need to create your own OAuth client IDs for these servers and configure them in the `remote_servers` dictionary. Create a new OAuth application in the servers Web UI and use the following redirect URI: `https://<your-jupyterlab-domain>/inveniordm-jupyterlab/auth/callback` and select Client Type `public`.

### Adding Remote Servers

- You can add additional InvenioRDM servers by specifying them in the `remote_servers` dictionary as demonstrated above.
- To allow the users of your JupyterLab instance to log in to the remote servers, you need to provide an OAuth client ID for each server that supports login.
  - In your servers Web UI, navigate to "Applications" and create a new OAuth application. Use the following redirect URI: `https://<your-jupyterlab-domain>/inveniordm-jupyterlab/auth/callback` and select Client Type `public`.

## List of Available Configuration Options

Find detailed information about the available configuaration options below.

## Remote servers

`remote_servers` is keyed by a stable server ID. New servers require `label`
and `base_url`. `oauth_client_id` is optional and enables login in `local`
request mode. A definition using a built-in ID (`zenodo` or `cds_repository`)
inherits unspecified built-in fields; configured fields always take precedence.

### Remote servers mode

`remote_servers_mode` controls membership and order:

- `extend`: keep built-ins first, merge matching definitions, and append new
  servers.
- `prepend`: put configured servers first, merge matching definitions, and add
  untouched built-ins afterward.
- `replace` (default): include only configured server IDs; matching built-ins
  still supply unspecified fields.

### Default remote server

The first resulting server is the default unless `default_remote_server` names
another included server.

### Built-in OAuth client IDs

Set `enable_builtin_local_oauth` to `True` to use the built-in OAuth client IDs
for Zenodo and CDS. It defaults to `True`. An `oauth_client_id` configured for
a remote server takes precedence over the built-in ID.

## Request mode

`c.InvenioRDMJupyterLab.request_mode` controls how requests are made to remote servers:

- `local` (default): requests are made directly to the remote server. Configure
  `oauth_client_id` for servers that support login.
- `proxy`: requests use the configured proxy. Every included server must define
  `proxy_url` and `proxy_session_cookie_name`.

Start JupyterLab with the configuration file:

```bash
jupyter lab --config=jupyter_server_config.py
```
