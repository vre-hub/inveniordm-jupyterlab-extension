c = get_config()  # noqa: F821

c.ZenodoJupyterLab.remote_servers = {
    "zenodo_production": {
        "label": "Production",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt",
        "proxy_url": "http://127.0.0.1:8003",
        "proxy_session_cookie_name": "zenodo_production_proxy_session",
    },
    "zenodo_sandbox": {
        "label": "Sandbox",
        "base_url": "https://sandbox.zenodo.org",
        "oauth_client_id": "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU",
        "proxy_url": "http://127.0.0.1:8001",
        "proxy_session_cookie_name": "zenodo_sandbox_proxy_session",
    },
    "cds_repository": {
        "label": "CDS",
        "base_url": "https://repository.cern",
        "oauth_client_id": "q4szrkotZqAuRA6HhGeajJsqTqEd6t6lTHHGLWD4",
        "proxy_url": "http://127.0.0.1:8004",
        "proxy_session_cookie_name": "cds_repository_proxy_session",
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
