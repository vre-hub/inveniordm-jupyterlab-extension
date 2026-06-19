#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export JUPYTERHUB_API_TOKEN="${ZENODO_JUPYTERHUB_SERVICE_API_TOKEN:?Please set the ZENODO_JUPYTERHUB_SERVICE_API_TOKEN environment variable here and in the JupyterHub environment.}"
export JUPYTERHUB_API_URL="${JUPYTERHUB_API_URL:-http://127.0.0.1:8081/hub/api}"
export JUPYTERHUB_SERVICE_NAME="${JUPYTERHUB_SERVICE_NAME:-zenodo-jupyterhub-service}"
export JUPYTERHUB_SERVICE_PREFIX="${JUPYTERHUB_SERVICE_PREFIX:-/services/zenodo-jupyterhub-service/}"

exec .venv/bin/python zenodo_jupyterhub_service/app.py
