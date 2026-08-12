from inveniordm_api_proxy.config import Config


def test_remote_server_can_be_configured(monkeypatch):
    monkeypatch.setenv("INVENIORDM_BASE_URL", "https://repository.example")
    monkeypatch.setenv("INVENIORDM_CLIENT_ID", "client-id")
    monkeypatch.setenv("INVENIORDM_PROXY_SESSION_COOKIE_NAME", "proxy_session")

    config = Config.from_environment()

    assert config.inveniordm_base_url == "https://repository.example"
    assert config.session_cookie_name == "proxy_session"


def test_remote_server_configuration_defaults_to_zenodo_sandbox(monkeypatch):
    for name in (
        "INVENIORDM_BASE_URL",
        "INVENIORDM_CLIENT_ID",
        "INVENIORDM_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    config = Config.from_environment()

    assert config.client_id == "ca8NzRHmqp6tVA0IE9XUlmbL74cGm9RqguC9DZlU"
    assert config.inveniordm_base_url == "https://sandbox.zenodo.org"
    assert config.session_cookie_name == "zenodo_sandbox_proxy_session"


def test_remote_server_configuration_defaults_to_sandbox(monkeypatch):
    monkeypatch.setenv("INVENIORDM_CLIENT_ID", "client-id")
    for name in (
        "INVENIORDM_BASE_URL",
        "INVENIORDM_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    config = Config.from_environment()

    assert config.inveniordm_base_url == "https://sandbox.zenodo.org"
    assert config.session_cookie_name == "zenodo_sandbox_proxy_session"
