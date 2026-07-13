# Project Architecture and Structure

What follows are notes on the architecture and structure of this project

## Rough Project Structure

This project consists of:

- A jupyterlab extension, consisting of a react/TS frontend and a python backend.
    - The backend is used to
        - forward calls to the Zenodo API proxy
        - create and manage downloaded deposition files so that they can be used inside the user's notebooks
        - implement other functions available in the UI (such as providing code snippets to import the downloaded files in the notebooks) so that the client can stay thin.
    - The client is designed as a thin client and should only provide UI elements for the user, so that all important logic is implemented by the server and is not scattered across client and server.
- An isolated Zenodo API Proxy that forwards the users requests to the Zenodo API and can store the Zenodo access tokens needed for that securely.

## Quirks of the System Architecture and why they exist

### Why do we need an extra proxy for the Zenodo API requests and token storage?

The Zenodo API requires the caller to send a Zenodo access token to execute requests on behalf of a user, e.g. for publishing depositions as the user or reading files the user, but not everyone has access to. We need to store this token somewhere securely.

The frontend is not the right place, because the users browser is the least controlled part of the system. Moreover, malicious extensions can read out the token and we cannot safeguard against that, since there is no isolation between jupyterlab extensions.

The extension backend is also not the right place. It is run in the same environment and with the same OS user as the jupyter server. This is not a problem if there is only one server per user, which is the recommended way to deploy a production Jupyter system. E.g. JupyterHub spins up a jupyter server per user by default and they are run in isolation. However, Juypter 5.0 introduces [Sharing Access to your Server](https://jupyterhub.readthedocs.io/en/stable/tutorial/sharing.html) for collaborative working, which can allow multiple users to execute code in the same server environment. Since this allows other users to read out environment variables and files, storing the single-user Zenodo access token here is insecure and shares it with the other users. Since this extension should be independent of the deployment configuration of the notebook execution backend behind JupyterLab, we should not store the access tokens there.

Therefore, a third, isolated component is needed to store the access token securely. Since the access tokens should not leave this environment for the API calls to be executed, they should be executed from the same place, making this a proxy for the Zenodo API. The proxy should be run in an isolated environment away from the users servers and can be used globally for all users using the deployed instance.

#### Interacting with the users notebook in the Frontend code: How does this align with "Thin Client"?

When a file is downloaded from zenodo, the user can click a button to add the path to this file as a hardcoded string into the current jupyter notebook, so they can use it without having to find the location themselves.

To implement this, the server exposes a route that generates this snippet (and if requested in the future, snippets for importing a dataset into specific frameworks like pandas or scipy). However, only the frontend can actually insert this snippet. This is because the extension backend in a jupyterlab extension does not have this capability (e.g. if the user has unsaved changes while working in the notebook, the extension backend does not know about them and inserting a cell would make the versions go out of sync). Therefore, the frontend itself has to insert the generated snippet. This violates the Thin Client principle but cannot be avoided and is an exception here.

#### Supporting both Production and Sandbox Zenodo: Isnt this an inconvenient feature to support long term?

There are two deployed instances of Zenodo, zenodo.org and sandbox.zenodo.org.

Developers of this extension and zenodo might want to use the Sandbox instance in the extension instead of Production. This is implemented in the following ways:

- When a user logs in, the component dealing with token storage checks if the access token is valid for the production or sandbox instance and saves which one it is alongside the access token. Whenever this access token is used for an API call, the correct instance is used for this call.
- Because it might be inconvenient in development to be tied to one instance depending on the access token, the developer settings of this extension allow to override whether sandbox or production is used for the outgoing requests. Once set, the override is appended to all requests to the extension backend and the backend respects this override for all incoming requests. (The override is implemented in a way so that it is also used for newly implemented routes in the future without having to manually specify sandbox_override as a request parameter.)

### Simple HTTP requests vs. SSE: Why not stick to the basics?

Most functionality provided by the extension backend is provided to the client via HTTP endpoints. However, some information should be kept in sync with the extension backend:

- Is the user logged in?
- Is a file present in the downloads?
- What is the progress of download of file XYZ?

It is possible for the client to keep the UI in sync with this information by frequently polling the HTTP endpoints. However, that creates unneccessary load for the server if the frequency is high and creates delays if the frequency is low. Therefore, Server-Sent Events (SSE) are used, which upgrade a HTTP connection to be kept alive, allowing the server to notify the client continuously about changes.

Sometimes, SSE are used to transmit information back to the client, e.g. the server sends frequent updates to the client to display the download progress correctly and includes the download progress in the data.

Other times, SSE are only used to notify the client that a certain information has changed and the value cached by the client might be invalid ("invalidation events"), not including the actual information in the event. For example, the SSE informing the client that the login status has changed, is used by the client to trigger multiple requests, e.g. to get the username and to request which zenodo instance is currently used.

This makes the network interface more complex but avoids performance issues and high network load.

### Multiple URLs pointing to the Jupyter Servers

OAuth redirect URIs are matched as exact strings. This means that URLs that point to the same Jupyter server from a networking perspective are still different OAuth origins, for example `http://localhost:8888/...` and `http://127.0.0.1:8888/...`.

This matters because browser cookies, JupyterLab frontend state, and the OAuth authorization code flow are all tied to the URL that was used. Mixing URLs during login can lead to confusing `invalid_grant` errors from Zenodo, because the authorization code is only valid for the exact client and redirect URI used when the login flow was started. This is a general OAuth requirement/ issue and we therefore cannot get rid of the underlying problem, therefore:

For production deployments, there should be one canonical public URL for the Jupyter service, and the OAuth callback URL registered in Zenodo should use that canonical URL. Other hostnames or aliases should redirect to the canonical URL before OAuth login starts. For local development, avoid switching between `localhost` and `127.0.0.1` in the same browser session.