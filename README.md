# Poetry Flake Template

This is a template for constructing a working environment for Python (version
3.11.6) development. Packaging and dependency management relies on [poetry](https://python-poetry.org/)
(version 1.7.0). [direnv](https://direnv.net/) can be used to a launch a dev
shell upon entering this directory (refer to `.envrc`). Otherwise run via:
```bash
$> nix develop
```

## Language Server

The [python-lsp-server](https://github.com/python-lsp/python-lsp-server)
(version v1.9.0) is included in this flake, along with the [python-lsp-black](https://github.com/python-lsp/python-lsp-black)
plugin for formatting purposes. `pylsp` is expected to be configured to use
[McCabe](https://github.com/PyCQA/mccabe), [pycodestyle](https://pycodestyle.pycqa.org/en/latest/),
and [pyflakes](https://github.com/PyCQA/pyflakes). Refer to your editor for
configuration details.

## Formatting

Formatting depends on the [black](https://black.readthedocs.io/en/stable/index.html)
(version 23.9.1) tool. A `pre-commit` hook is included in `.githooks` that can
be used to format all `*.py` files prior to commit. Install via:
```bash
$> git config --local core.hooksPath .githooks/
```
If running [direnv](https://direnv.net/), this hook is installed automatically
when entering the directory.
