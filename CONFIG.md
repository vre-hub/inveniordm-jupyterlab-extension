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
    "zenodo_production": {
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

The bundled Zenodo OAuth client ID only works for JupyterLab at
`http://localhost:8888` or `http://127.0.0.1:8888`. For any other URL, register
your own Zenodo OAuth application for that URL and replace the client ID.

Start JupyterLab with the config:

```bash
jupyter lab --config=jupyter_server_config.py
```
