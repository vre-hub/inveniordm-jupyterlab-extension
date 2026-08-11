# Contributing

## Development install

Note: You will need Node.js to build the extension package.
You may install it from [nodejs.org](https://nodejs.org/en/download). We
recommend using the latest LTS version of Node.js.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the inveniordm_jupyterlab directory

# Set up a virtual environment and install package in development mode
python -m venv .venv
source .venv/bin/activate
pip install --editable ".[dev,test]"

# Link your development version of the extension with JupyterLab
jupyter-builder develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable inveniordm_jupyterlab

# Rebuild extension Typescript source after making changes
# IMPORTANT: Unlike the steps above which are performed only once, do this step
# every time you make a change.
jlpm build
```

### Building the Tailwind CSS

The extension's Tailwind source is `style/tailwind.css`. After adding or
changing Tailwind classes in the TypeScript or TSX source, activate the Python
virtual environment (so that `jlpm` is available) and regenerate the committed
stylesheet:

```bash
source .venv/bin/activate
jlpm tailwindcss --input style/tailwind.css --output style/index.css
```

`style/index.css` is generated, but it is intentionally committed because it
is the stylesheet loaded and published by the JupyterLab extension. Include
the updated file in the same commit as the Tailwind source or class changes.

To regenerate the stylesheet automatically while developing, run:

```bash
source .venv/bin/activate
jlpm tailwindcss --input style/tailwind.css --output style/index.css --watch
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Different users on the JupyterLab instance

- Use different browser profiles to simulate different users using the instance. Each profile should get a different username
  - TODO check if this actually behaves similarly enough to e.g. production jupyterhubs

## Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable inveniordm_jupyterlab
pip uninstall inveniordm_jupyterlab
```

In development mode, you will also need to remove the symlink created by `jupyter-builder develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `inveniordm_jupyterlab` within that folder.

## Testing the extension

### Server tests

This extension is using [Pytest](https://docs.pytest.org/) for Python code testing.

Install test dependencies (needed only once):

```sh
pip install -e ".[test]"
# Each time you install the Python package, you need to restore the front-end extension link
jupyter-builder develop . --overwrite
```

To execute them, run:

```sh
pytest -vv -r ap --cov inveniordm_jupyterlab
```

#### Frontend tests

This extension is using [Jest](https://jestjs.io/) for JavaScript code testing.

To execute them, execute:

```sh
jlpm
jlpm test
```

### Integration tests

This extension uses [Playwright](https://playwright.dev/docs/intro) for the integration tests (aka user level tests).
More precisely, the JupyterLab helper [Galata](https://github.com/jupyterlab/jupyterlab/tree/master/galata) is used to handle testing the extension in JupyterLab.

More information is provided within the [ui-tests](./ui-tests/README.md) README.

## Packaging the extension

See [RELEASE](RELEASE.md)
