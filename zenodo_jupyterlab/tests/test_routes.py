import json


async def test_hello(jp_fetch):
    # When
    response = await jp_fetch("zenodo-jupyterlab", "hello")

    # Then
    assert response.code == 200
    payload = json.loads(response.body)
    assert payload == {
        "data": (
            "Hello, world!"
            " This is the '/zenodo-jupyterlab/hello' endpoint."
            " Try visiting me in your browser!"
        ),
    }


async def test_cancel_unknown_job(jp_fetch):
    response = await jp_fetch(
        "zenodo-jupyterlab",
        "jobs",
        "unknown",
        "cancel",
        method="POST",
        body="",
        raise_error=False,
    )

    assert response.code == 404
    assert json.loads(response.body) == {"message": "Unknown job"}


async def test_find_active_download_jobs(jp_fetch):
    response = await jp_fetch(
        "zenodo-jupyterlab",
        "jobs",
        params={
            "job_type": "download",
            "record_id": "123",
            "file_key": "file-1",
            "status": "active",
            "latest": "true",
        },
    )

    assert response.code == 200
    assert json.loads(response.body) == {"job_ids": []}
