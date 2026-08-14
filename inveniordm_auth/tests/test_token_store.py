import json

from inveniordm_auth.token_store import FileTokenStore


def test_file_token_store_persists_multiple_tokens(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)

    store.set_token(
        "inveniordm_production",
        "alice-token",
        True,
        remote_server_id="inveniordm_production",
        inveniordm_user_id="123",
    )
    store.set_token(
        "inveniordm_sandbox",
        "bob-token",
        False,
        remote_server_id="inveniordm_sandbox",
    )

    production_token = store.get_token("inveniordm_production")
    assert production_token is not None
    assert production_token.access_token == "alice-token"
    assert production_token.access_token_valid is True
    assert production_token.remote_server_id == "inveniordm_production"
    assert production_token.inveniordm_user_id == "123"

    sandbox_token = store.get_token("inveniordm_sandbox")
    assert sandbox_token is not None
    assert sandbox_token.access_token == "bob-token"
    assert sandbox_token.access_token_valid is False
    assert sandbox_token.remote_server_id == "inveniordm_sandbox"

    assert json.loads(path.read_text()) == {
        "tokens": {
            "inveniordm_production": {
                "access_token": "alice-token",
                "access_token_valid": True,
                "remote_server_id": "inveniordm_production",
                "inveniordm_user_id": "123",
            },
            "inveniordm_sandbox": {
                "access_token": "bob-token",
                "access_token_valid": False,
                "remote_server_id": "inveniordm_sandbox",
                "inveniordm_user_id": None,
            },
        },
    }


def test_file_token_store_returns_none_for_missing_file(tmp_path):
    assert FileTokenStore(tmp_path / "tokens.json").get_token("user") is None


def test_file_token_store_removes_one_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.set_token("alice", "alice-token", True, "production")
    store.set_token("bob", "bob-token", True, "sandbox")

    store.remove_token("alice")

    assert store.get_token("alice") is None
    assert store.get_token("bob") is not None
    assert path.exists()


def test_file_token_store_removes_file_after_last_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.set_token("user", "token", True, "production")

    store.remove_token("user")

    assert store.get_token("user") is None
    assert not path.exists()
