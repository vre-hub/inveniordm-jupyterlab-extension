import json
from types import SimpleNamespace
from unittest.mock import Mock

from inveniordm_auth import OAuthCallback
from inveniordm_auth.remote_servers import RemoteServerRegistry
from inveniordm_jupyterlab.inveniordm_auth import local_auth_controller
from inveniordm_jupyterlab.inveniordm_auth.local_auth_controller import (
    LocalInvenioRDMAuthController,
)


def test_login_without_client_id_returns_error_before_building_oauth_config(
    monkeypatch,
):
    remote_servers = RemoteServerRegistry(
        {
            "public_repository": {
                "label": "Public repository",
                "base_url": "https://public.example",
            }
        }
    )
    oauth_config = Mock()
    monkeypatch.setattr(local_auth_controller, "OAuthClientConfig", oauth_config)
    responses = []
    statuses = []
    handler = SimpleNamespace(
        get_query_argument=lambda name, default=None: default,
        set_status=statuses.append,
        set_header=Mock(),
        finish=responses.append,
        request=SimpleNamespace(
            protocol="http",
            host="localhost:8888",
            headers={},
        ),
        settings={"base_url": "/"},
    )
    controller = LocalInvenioRDMAuthController(Mock(), remote_servers)

    controller.login(handler)

    assert statuses == [503]
    assert json.loads(responses[0]) == {
        "message": (
            "OAuth login is not configured for remote server 'public_repository'."
        )
    }
    oauth_config.assert_not_called()


def test_completed_logins_are_stored_by_remote_server(remote_servers):
    token_store = Mock()
    controller = LocalInvenioRDMAuthController(token_store, remote_servers)
    handler = Mock()

    controller._complete_oauth_login(
        handler,
        OAuthCallback("/lab", "123", "token", {}),
        remote_server_id="cds",
    )

    token_store.set_token.assert_called_once_with(
        "cds",
        "token",
        True,
        remote_server_id="cds",
        inveniordm_user_id="123",
    )
    handler.redirect.assert_called_once_with("/lab")


def test_logout_removes_only_selected_remote_server(remote_servers):
    token_store = Mock()
    controller = LocalInvenioRDMAuthController(token_store, remote_servers)
    handler = Mock()
    handler.get_query_argument.side_effect = lambda name, default=None: (
        "cds" if name == "remote_server" else default
    )

    controller.logout(handler)

    token_store.remove_token.assert_called_once_with("cds")
    handler.finish.assert_called_once_with(json.dumps({"authenticated": False}))
