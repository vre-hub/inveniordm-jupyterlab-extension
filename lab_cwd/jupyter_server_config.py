c = get_config()  # noqa: F821
c.ZenodoJupyterLab.remote_servers_mode = "extend"
c.ZenodoJupyterLab.default_remote_server = "inveniordm_local"
c.ZenodoJupyterLab.remote_servers = {
    "inveniordm_local": {
        "label": "InvenioRDM Local",
        "base_url": "http://127.0.0.1:80",
        "oauth_client_id": "jupyterlab-extension",
        "proxy_url": "http://127.0.0.1:8006",
        "proxy_session_cookie_name": "invenioRDM_local_proxy_session",
    },
}
