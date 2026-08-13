# Container image for the InvenioRDM API proxy.
#
# Deliberately does NOT install the JupyterLab extension: the proxy only needs
# inveniordm_api_proxy and inveniordm_auth, so building this image does not
# require node/yarn or the labextension build hook from pyproject.toml.
#
# Build from the repository root:
#   docker build -f deploy/docker/Dockerfile -t inveniordm-api-proxy .

FROM python:3.12-slim

# tornado: the proxy's web server.
# jupyter-core: token_store imports jupyter_data_dir for its default path.
RUN pip install --no-cache-dir \
        "tornado>=6.4,<7" \
        "jupyter-core>=5,<6"

WORKDIR /app
COPY inveniordm_api_proxy/ /app/inveniordm_api_proxy/
COPY inveniordm_auth/ /app/inveniordm_auth/

# Drop the test packages; they are not needed at runtime and pull no weight.
RUN find /app -type d -name tests -prune -exec rm -rf {} + \
    && find /app -type d -name __pycache__ -prune -exec rm -rf {} +

# Matches the securityContext in deploy/helm/inveniordm-api-proxy.
# NB: the Debian base already ships a system user named "proxy" (uid 13), so
# this account needs a different name.
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin inveniordm
USER 1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PROXY_HOST=0.0.0.0 \
    PROXY_PORT=8001

EXPOSE 8001

CMD ["python", "-m", "inveniordm_api_proxy"]
