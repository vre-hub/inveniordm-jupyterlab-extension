from zenodo_api_proxy.config import Config


def test_remote_server_can_be_configured(monkeypatch):
    monkeypatch.setenv("ZENODO_BASE_URL", "https://repository.example")
    monkeypatch.setenv("ZENODO_CLIENT_ID", "client-id")
    monkeypatch.setenv("ZENODO_PROXY_SESSION_COOKIE_NAME", "proxy_session")

    config = Config.from_environment()

    assert config.zenodo_base_url == "https://repository.example"
    assert config.session_cookie_name == "proxy_session"


def test_remote_server_configuration_is_required(monkeypatch):
    for name in (
        "ZENODO_BASE_URL",
        "ZENODO_CLIENT_ID",
        "ZENODO_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    try:
        Config.from_environment()
    except ValueError as error:
        assert str(error) == "Set ZENODO_CLIENT_ID before starting the proxy"
    else:
        raise AssertionError("Expected missing proxy configuration to be rejected")


def test_remote_server_configuration_defaults_to_sandbox(monkeypatch):
    monkeypatch.setenv("ZENODO_CLIENT_ID", "client-id")
    for name in (
        "ZENODO_BASE_URL",
        "ZENODO_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    config = Config.from_environment()

    assert config.zenodo_base_url == "https://sandbox.zenodo.org"
    assert config.session_cookie_name == "zenodo_sandbox_proxy_session"
