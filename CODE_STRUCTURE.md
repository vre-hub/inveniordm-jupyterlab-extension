# Notes on the Code Structure

- `inveniordm_auth` is an extra Python package for authentication code shared by the API proxy and the JupyterLab extension backend. Shared OAuth configuration, remote-server definitions, and token handling belong here; application-specific handlers and controllers stay in their respective packages.
- `src/api_calls.ts` is the frontend transport boundary
  - Components must not call its functions directly: API access and stateful behavior belong in `src/core`, exposed to components through hooks or other small interfaces.
  - Components may use `import type` from `api_calls.ts` because this creates no runtime dependency.
- `src/core` contains the core application logic and `src/components` the presentation logic.
  - `src/core` must therefore not import from `src/components`. Core code should be UI-independent; component props and rendering choices belong in the component layer.
  - Components may depend on `core`, and top-level widgets may compose both.

Before adding a feature, decide whether it is shared authentication, backend application logic, frontend transport/state, or presentation. Put it in the lowest appropriate layer and keep tests beside the behavior they cover.
