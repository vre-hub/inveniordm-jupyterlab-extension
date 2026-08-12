c = get_config()  # noqa: F821
c.InvenioRDMJupyterLab.remote_servers = {
    "zenodo": {
        "label": "Zenodo",
        "base_url": "https://zenodo.org",
        "oauth_client_id": "HaWBPRb7lsif7cqTypUNeFni9PJOoTm5IcjTJrtt",
    },
    "cds": {
        "label": "CDS",
        "base_url": "https://repository.cern",
        "oauth_client_id": "q4szrkotZqAuRA6HhGeajJsqTqEd6t6lTHHGLWD4",
    },
    "zenodo_sandbox": {
        "label": "Zenodo Sandbox",
        "base_url": "https://sandbox.zenodo.org",
        "oauth_client_id": "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU",
    },
    "cds_sandbox": {
        "label": "CDS Sandbox",
        "base_url": "https://sandbox-cds-rdm.web.cern.ch",
        "oauth_client_id": "J5nzeas8LpcGllJysNJzj52YT0qpvJbVA0AN0F5y",
    },
    "inveniordm_local": {
        "label": "InvenioRDM Local",
        "base_url": "http://127.0.0.1:80",
        "oauth_client_id": "jupyterlab-extension",
    },
}
