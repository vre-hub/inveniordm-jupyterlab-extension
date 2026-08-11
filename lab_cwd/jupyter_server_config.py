c = get_config()  # noqa: F821
c.InvenioRDMJupyterLab.remote_servers_mode = "extend"
c.InvenioRDMJupyterLab.remote_servers = {
    "zenodo_sandbox": {
        "label": "Zenodo Sandbox",
        "base_url": "https://sandbox.zenodo.org",
        "oauth_client_id": "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU",
        "proxy_url": "http://127.0.0.1:8001",
        "proxy_session_cookie_name": "zenodo_sandbox_proxy_session",
    },
    "cds_repository_sandbox": {
        "label": "CDS Sandbox",
        "base_url": "https://sandbox-cds-rdm.web.cern.ch",
        "oauth_client_id": "J5nzeas8LpcGllJysNJzj52YT0qpvJbVA0AN0F5y",
        "proxy_url": "http://127.0.0.1:8005",
        "proxy_session_cookie_name": "cds_repository_sandbox_proxy_session",
    },
    "inveniordm_local": {
        "label": "InvenioRDM Local",
        "base_url": "http://127.0.0.1:80",
        "oauth_client_id": "jupyterlab-extension",
        "proxy_url": "http://127.0.0.1:8006",
        "proxy_session_cookie_name": "invenioRDM_local_proxy_session",
    },
}
