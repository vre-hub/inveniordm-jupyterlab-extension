import json

from zenodo_jupyterlab.zenodo_requests.token_store import FileTokenStore


def test_file_token_store_persists_validity(tmp_path):
    store = FileTokenStore(tmp_path / "tokens.json")

    store.set_access_token("user", "token", True)
    store.set_access_token_validity("user", False)

    token = store.get_token("user")
    assert token is not None
    assert token.access_token == "token"
    assert token.access_token_valid is False

    data = json.loads((tmp_path / "tokens.json").read_text())
    assert data == {
        "user": {
            "access_token": "token",
            "access_token_valid": False,
        }
    }


def test_file_token_store_reads_old_string_tokens_as_valid(tmp_path):
    path = tmp_path / "tokens.json"
    path.write_text(json.dumps({"user": "old-token"}))

    token = FileTokenStore(path).get_token("user")

    assert token is not None
    assert token.access_token == "old-token"
    assert token.access_token_valid is True
