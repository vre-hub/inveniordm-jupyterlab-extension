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

Zenodo and the CERN Document Server are configured by default. Public record
search and download do not require login, and the built-in OAuth client IDs
enable login in local request mode.

The server extension reads remote servers from
`InvenioRDMJupyterLab.remote_servers` in the Jupyter Server configuration.
Setting this option replaces the complete default mapping. Each entry is keyed
by its server ID and requires a `label` and `base_url`. The `oauth_client_id` is
optional and enables login for that server.

For development, the config in `lab_cwd` provides InvenioRDM production and
sandbox, CDS production and sandbox, and the local InvenioRDM server. Start Lab
from that directory with:

```bash
jupyter lab --config=jupyter_server_config.py
```

Set `default_remote_server` to a configured server ID to choose the default. If
it is omitted, the first configured remote server is used when the request does
not specify a server and no authenticated session is found.

## Contributing

If you would like to contribute to this extension, please refer to the [Contributing Guide](CONTRIBUTING.md).
