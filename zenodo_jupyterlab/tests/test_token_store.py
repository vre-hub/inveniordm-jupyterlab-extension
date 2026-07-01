import json

from zenodo_jupyterlab.zenodo_requests.token_store import FileTokenStore


def test_file_token_store_persists_validity(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)

    store.set_access_token("token", True)
    store.set_access_token_validity(False)

    token = store.get_token()
    assert token is not None
    assert token.access_token == "token"
    assert token.access_token_valid is False

    assert json.loads(path.read_text()) == {
        "access_token": "token",
        "access_token_valid": False,
        "sandbox": False,
    }


def test_file_token_store_returns_none_for_missing_file(tmp_path):
    assert FileTokenStore(tmp_path / "tokens.json").get_token() is None


def test_file_token_store_removes_token(tmp_path):
    path = tmp_path / "tokens.json"
    store = FileTokenStore(path)
    store.set_access_token("token", True)

    store.remove_access_token()

    assert store.get_token() is None
    assert not path.exists()
