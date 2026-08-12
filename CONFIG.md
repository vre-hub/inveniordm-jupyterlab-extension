# Configuration quickstart

Create or edit `jupyter_server_config.py` and define your institution's
InvenioRDM server:

```python
c = get_config()  # noqa: F821
c.InvenioRDMJupyterLab.remote_servers = {
    "institution": {
        "label": "My institution",
        "base_url": "https://repository.example.org",
        "oauth_client_id": "your-institution-oauth-client-id",
    },
    # Keep this entry if you also want to use Zenodo.
    "zenodo": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "5LkeWfl5Yvhiz42JkAYQI64UYAsyxll2opUsNdmN",
    },
}
c.InvenioRDMJupyterLab.default_remote_server = "institution"
```

Setting `remote_servers` replaces all defaults, so copy the Zenodo entry above
if you want to keep using it. `oauth_client_id` is optional for anonymous-only
access.

## Configuring OAuth client IDs for Zenodo and CDS

The bundled Zenodo OAuth client ID, as well as the CDS OAuth client ID, only works for JupyterLab at
`http://localhost:8888` or `http://127.0.0.1:8888`.

This is intended for people running JupyterLab locally, e.g. on their own computer, with default JupyterLab settings, so that the extension works out of the box for them. If you are running JupyterLab on a different URL, you will need to register your own OAuth application for that URL and replace the client ID.

## Running JupyterLab with the config

Start JupyterLab with the config:

```bash
jupyter lab --config=jupyter_server_config.py
```
