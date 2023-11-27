# chesscom-scraper

**Caution! Be careful running this script.**

We intentionally delay each request sent anywhere from 10 to 15 seconds. Make
sure any adjustments to this script appropriately rate-limit.

## Overview

This is a simple web scraper for [chess.com](https://www.chess.com/coaches)
coaches. Running:
```bash
$> python3 main.py
```
will query [chess.com](https://www.chess.com) for all listed coaches as well as
specific information about each of them (their profile, recent activity, and
stats). The result will be found in a newly created `data` directory with the
following structure:
```
data
├── coach
│   ├── <member_name>
│   │   ├── <member_name>.html
│   │   ├── activity.json
│   │   └── stats.json
│   ├── ...
└── pages
    ├── <n>.txt
    ├── ...
```

Here, `member_name` corresponds to the name of the coach whereas `pages`
contains a fragmented list of URLs to coach profiles.

## Development

This script was written using Python (version 3.11.6). Packaging and dependency
management relies on [poetry](https://python-poetry.org/) (version 1.7.0).
[direnv](https://direnv.net/) can be used to a launch a dev shell upon entering
this directory (refer to `.envrc`). Otherwise run via:
```bash
$> nix develop
```

### Language Server

The [python-lsp-server](https://github.com/python-lsp/python-lsp-server)
(version v1.9.0) is included in this flake, along with the [python-lsp-black](https://github.com/python-lsp/python-lsp-black)
plugin for formatting purposes. `pylsp` is expected to be configured to use
[McCabe](https://github.com/PyCQA/mccabe), [pycodestyle](https://pycodestyle.pycqa.org/en/latest/),
and [pyflakes](https://github.com/PyCQA/pyflakes). Refer to your editor for
configuration details.

### Formatting

Formatting depends on the [black](https://black.readthedocs.io/en/stable/index.html)
(version 23.9.1) tool. A `pre-commit` hook is included in `.githooks` that can
be used to format all `*.py` files prior to commit. Install via:
```bash
$> git config --local core.hooksPath .githooks/
```
If running [direnv](https://direnv.net/), this hook is installed automatically
when entering the directory.
