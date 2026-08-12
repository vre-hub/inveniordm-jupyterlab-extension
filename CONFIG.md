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
```

## Remote servers

`remote_servers` is keyed by a stable server ID. New servers require `label`
and `base_url`. `oauth_client_id` is optional and enables login in `local`
request mode. A definition using a built-in ID (`zenodo` or `cds_repository`)
inherits unspecified built-in fields; configured fields always take precedence.

`remote_servers_mode` controls membership and order:

- `extend`: keep built-ins first, merge matching definitions, and append new
  servers.
- `prepend`: put configured servers first, merge matching definitions, and add
  untouched built-ins afterward.
- `replace` (default): include only configured server IDs; matching built-ins
  still supply unspecified fields.

The first resulting server is the default unless `default_remote_server` names
another included server.

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
