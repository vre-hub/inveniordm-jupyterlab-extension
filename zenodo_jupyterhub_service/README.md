# JupyterHub Development

Tiny local JupyterHub with an authenticated Zenodo JupyterHub service.

## Development Setup

Terminal 1:

```bash
pip install jupyterhub
export ZENODO_JUPYTERHUB_SERVICE_API_TOKEN="dev-zenodo-jupyterhub-service-token-change-me"
cd zenodo_jupyterhub_service
jupyterhub -f jupyterhub_config.py
```

Terminal 2:

```bash
export ZENODO_JUPYTERHUB_SERVICE_API_TOKEN="dev-zenodo-jupyterhub-service-token-change-me"
zenodo_jupyterhub_service/run_zenodo_jupyterhub_service.sh
```

In the same venv, the jupyterlab zenodo extension needs to be installed.

Log in with any username and password `jupyter`, then visit the **extension** route (not the service directly!):

- `http://127.0.0.1:8000/user/<username>/zenodo-jupyterlab/whoami`

## Production Setup

When running this in production, `zenodo_jupyterhub_service/run_zenodo_jupyterhub_service.sh` (or the service python script) should be run in an isolated environment, e.g. a docker container. This is important because JupyterHub might be running in the same or similar environment as the users Notebooks/ Jupyter Servers, and they might be able to access the sensitive data that the service deals with.

To make this work, the container and the environment the JupyterHub runs in both need to have the env variable `ZENODO_JUPYTERHUB_SERVICE_API_TOKEN` set. This will make JupyterHub delegate the necessary requests to the service.

## Project Structure

This currently contains

- the jupyterhub service (python code)
- a jupyterhub config that should be used while developing the application

and it lives in the repo of the juypterlab extension.

//TODO restructure the project so it splits code from extension and service more cleanly

to make this more clear, the actual structure should probably be:

```sh
zenodo_jupyterlab_extension/ # repo root
  zenodo_jupyterlab_extension/ # created from copier template
    zenodo_jupyterlab/
      routes.py
      ...
    src/
      ...
  zenodo_jupyterhub_service/ # code for jupyterhub service
    zenodo_jupyterhub_service/
      app.py
      ...
  zenodo_common/ # shared code (zenodo api calls, token storage)
    zenodo_client.py
    token_store.py
```

## How the authentication works

The python backend of the jupyterlab extension sends a request to the service, containing a JUPYTERHUB_API_TOKEN. The service is able to identify which jupyter user is behind that request.

(If the frontend of the jupyterlab extension would instead make those calls, it would have to go through the OAuth flow to get a service cookie. This is also quite easy and does not even need the users permission if the config is set to "oauth_no_confirm": True).
