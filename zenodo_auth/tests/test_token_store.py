import json

from zenodo_auth.token_store import (
    BoundedTokenStore,
    FileTokenStore,
)


def test_file_token_store_persists_multiple_tokens(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)

    store.set_token("alice", "alice-token", True, zenodo_user_id="123")
    store.set_token("bob", "bob-token", False, sandbox=True)

    alice_token = store.get_token("alice")
    assert alice_token is not None
    assert alice_token.access_token == "alice-token"
    assert alice_token.access_token_valid is True
    assert alice_token.sandbox is False
    assert alice_token.zenodo_user_id == "123"

    bob_token = store.get_token("bob")
    assert bob_token is not None
    assert bob_token.access_token == "bob-token"
    assert bob_token.access_token_valid is False
    assert bob_token.sandbox is True

    assert json.loads(path.read_text()) == {
        "tokens": {
            "alice": {
                "access_token": "alice-token",
                "access_token_valid": True,
                "sandbox": False,
                "zenodo_user_id": "123",
            },
            "bob": {
                "access_token": "bob-token",
                "access_token_valid": False,
                "sandbox": True,
                "zenodo_user_id": None,
            },
        },
    }


def test_file_token_store_returns_none_for_missing_file(tmp_path):
    assert FileTokenStore(tmp_path / "tokens.json").get_token("user") is None


def test_file_token_store_removes_one_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.set_token("alice", "alice-token", True)
    store.set_token("bob", "bob-token", True)

    store.remove_token("alice")

    assert store.get_token("alice") is None
    assert store.get_token("bob") is not None
    assert path.exists()


def test_file_token_store_removes_file_after_last_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.set_token("user", "token", True)

    store.remove_token("user")

    assert store.get_token("user") is None
    assert not path.exists()


def test_bounded_token_store_uses_single_bound_token(tmp_path):
    path = tmp_path / "tokens.json"
    multi_store = FileTokenStore(path)
    store = BoundedTokenStore(multi_store, "local-user")

    store.set_token("token", True, sandbox=True, zenodo_user_id="456")

    token = store.get_token()
    assert token is not None
    assert token.access_token == "token"
    assert token.access_token_valid is True
    assert token.sandbox is True
    assert token.zenodo_user_id == "456"
    assert multi_store.get_token("local-user") == token


def test_file_token_store_reads_legacy_single_token_file(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text(
        json.dumps(
            {
                "access_token": "legacy-token",
                "access_token_valid": False,
                "sandbox": True,
            }
        )
    )

    token = FileTokenStore(path).get_token("user")

    assert token is not None
    assert token.access_token == "legacy-token"
    assert token.access_token_valid is False
    assert token.sandbox is True
    assert token.zenodo_user_id is None
