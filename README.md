# inveniordm_jupyterlab

A JupyterLab extension that integrates InvenioRDM-based services like Zenodo or CDS into JupyterLab.

This extension is composed of a Python package named `inveniordm_jupyterlab`
for the server extension and a NPM package named `inveniordm_jupyterlab`
for the frontend extension.

## Requirements

- JupyterLab >= 4.0.0

## Install

To install the extension, execute:

```bash
pip install inveniordm_jupyterlab
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall inveniordm_jupyterlab
```

## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```

## Remote server configuration

Zenodo and the CERN Document Server are available as public, anonymous remote
servers by default. Public record search and download do not require login.

The server extension reads remote server definitions from
`InvenioRDMJupyterLab.remote_servers` in the Jupyter Server configuration.
Definitions with the same ID as a built-in server are merged with that server,
so they can set only the fields they want to override or add. Set
`remote_servers_mode` to control which servers are included and their order:
`extend` keeps the built-ins first and appends new servers, `prepend` puts
configured servers first and then adds untouched built-ins, and `replace`
includes only configured server IDs. In all three modes, configured fields take
precedence over built-in fields. New server IDs need a `label` and `base_url`;
`oauth_client_id` is optional and enables login for that server in local request
mode.

For development, the config in `lab_cwd` provides InvenioRDM production and
sandbox, CDS production and sandbox, and the local InvenioRDM server. Start Lab
from that directory with:

```bash
jupyter lab --config=jupyter_server_config.py
```

The first configured remote server is used as the default when the request does
not specify a server and no authenticated session is found.

## Contributing

If you would like to contribute to this extension, please refer to the [Contributing Guide](CONTRIBUTING.md).
