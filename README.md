# inveniordm_jupyterlab

[![Github Actions Status](https://github.com/ejuet/inveniordm-jupyterlab-extension-prototype/workflows/Build/badge.svg)](https://github.com/ejuet/inveniordm-jupyterlab-extension-prototype/actions/workflows/build.yml)

Integrates InvenioRDM into JupyterLab.

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

The server extension reads its available remote servers from
`InvenioRDMJupyterLab.remote_servers` in the Jupyter Server configuration.

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
