# coach-scraper

**Caution! Be careful running this script.**

We intentionally delay each batch of requests. Make sure any adjustments to this
script appropriately rate-limit.

## Overview

This is a simple web scraper for coaches listed on:

* [chess.com](https://www.chess.com/coaches)
* [lichess.org](https://www.lichess.org/coach)

The program searches for coach usernames as well as specific information about
each of them (their profile, recent activity, and stats). Data is streamed into
a Postgres instance. Downloaded content is found in a newly created `data`
directory with the following structure:
```
data
└── <site>
│   ├── coaches
│   │   ├── <username>
│   │   │   ├── <username>.html
│   │   │   └── ...
│   │   ├── ...
└── pages
    ├── <n>.txt
    ├── ...
```

## Quickstart

Included in the development shell of this flake is a [Postgres](https://www.postgresql.org/)
client (version 15.5). Generate an empty Postgres cluster at `/db` by running
```bash
$ pg_ctl -D db init
```
To start the database, run the following:
```bash
$ pg_ctl -D db -l db/logfile -o --unix_socket_directories=@scraper start
```
In the above command, `@scraper` refers to an [abstract socket name](https://www.postgresql.org/docs/15/runtime-config-connection.html#GUC-UNIX-SOCKET-DIRECTORIES).
Rename to whatever is appropriate for your use case. To then connect to this
database instance, run:
```bash
$ psql -h @scraper
```
To later shut the database down, run:
```bash
$ pg_ctl -D db stop
```
Initialize the table that scraped content will be streamed into:
```bash
$ psql -h @scraper -f sql/init.sql
```
If you have nix available, you can now run the scraper via
```bash
$ nix run . -- ...
```
Otherwise, ensure you have [poetry](https://python-poetry.org/) on your machine
and instead run the following:
```bash
$ poetry run python3 -m app ...
```

## Development

[nix](https://nixos.org/) is used for development. The included `flakes.nix`
file automatically loads in Python (version 3.11.6) with packaging and
dependency management handled by poetry (version 1.7.0). [direnv](https://direnv.net/)
can be used to a launch a dev shell upon entering this directory (refer to
`.envrc`). Otherwise run via:
```bash
$ nix develop
```

### Language Server

The [python-lsp-server](https://github.com/python-lsp/python-lsp-server)
(version v1.9.0) is included in this flake, along with the [python-lsp-black](https://github.com/python-lsp/python-lsp-black)
and [pyls-isort](https://github.com/paradoxxxzero/pyls-isort) plugins.
Additionally, `pylsp` is expected to be configured to use:

* [McCabe](https://github.com/PyCQA/mccabe),
* [pycodestyle](https://pycodestyle.pycqa.org/en/latest/), and
* [pyflakes](https://github.com/PyCQA/pyflakes).

Refer to your editor for configuration details.

### Formatting

Formatting depends on the [black](https://black.readthedocs.io/en/stable/index.html)
(version 23.9.1) tool. A `pre-commit` hook is included in `.githooks` that can
be used to format all `*.py` files prior to commit. Install via:
```bash
$ git config --local core.hooksPath .githooks/
```
If running [direnv](https://direnv.net/), this hook is installed automatically
when entering the directory.
