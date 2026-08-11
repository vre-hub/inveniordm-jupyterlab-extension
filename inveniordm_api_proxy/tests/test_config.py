from inveniordm_api_proxy.config import Config


def test_remote_server_can_be_configured(monkeypatch):
    monkeypatch.setenv("INVENIORDM_BASE_URL", "https://repository.example")
    monkeypatch.setenv("INVENIORDM_CLIENT_ID", "client-id")
    monkeypatch.setenv("INVENIORDM_PROXY_SESSION_COOKIE_NAME", "proxy_session")

    config = Config.from_environment()

    assert config.inveniordm_base_url == "https://repository.example"
    assert config.session_cookie_name == "proxy_session"


def test_remote_server_configuration_is_required(monkeypatch):
    for name in (
        "INVENIORDM_BASE_URL",
        "INVENIORDM_CLIENT_ID",
        "INVENIORDM_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    try:
        Config.from_environment()
    except ValueError as error:
        assert str(error) == "Set INVENIORDM_CLIENT_ID before starting the proxy"
    else:
        raise AssertionError("Expected missing proxy configuration to be rejected")


def test_remote_server_configuration_defaults_to_sandbox(monkeypatch):
    monkeypatch.setenv("INVENIORDM_CLIENT_ID", "client-id")
    for name in (
        "INVENIORDM_BASE_URL",
        "INVENIORDM_PROXY_SESSION_COOKIE_NAME",
    ):
        monkeypatch.delenv(name, raising=False)

    config = Config.from_environment()

    assert config.inveniordm_base_url == "https://sandbox.inveniordm.org"
    assert config.session_cookie_name == "inveniordm_sandbox_proxy_session"
