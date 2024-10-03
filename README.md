# pylsp-docformatter

Docformatter plugin for the Python LSP Server.

This is a plugin for [Python LSP Server](https://github.com/python-lsp/python-lsp-server).

## Installation

To use this plugin, you need to install this plugin in the same virtualenv as python-lsp-server itself.

``` bash
pip install pylsp-docformatter
```

Then run `python-lsp-server` as usual, the plugin will be auto-discovered by
`python-lsp-server` if you've installed it to the right environment. Refer to
`python-lsp-server` and your IDE/text editor documentation on how to setup
`python-lsp-server`.

## Configuration

Configuration is read from the [Python LSP Server configuration](https://github.com/python-lsp/python-lsp-server/#configuration).

The following settings are available:

- `pylsp.plugins.pylsp_docformatter.enabled`: Enable or disable the plugin. Default is `true`.
- `pylsp.plugins.pylsp_docformatter.config_file`: Path to the configuration file for `docformatter`
  (`--config` option to `docformatter, see https://docformatter.readthedocs.io/en/latest/configuration.html
  for details). Unset by default.

## Features

This plugin adds docstring formatting via [docformatter](https://docformatter.readthedocs.io) to `pylsp`.

## Developing

Clone the repository:

``` bash
git clone https://github.com/heindsight/pylsp-docformatter pylsp-docformatter
```

Install development dependencies with:

``` bash
cd pylsp-docformatter
tox devenv
```

This will create a virtual environment in `venv/` with an editable install of the plugin and all development dependencies.

Alternatively you can create the virtual environment manually:

``` bash
cd pylsp-docformatter
python -m venv venv
pip install -e .[dev]
```

### Enabling logging

To enable logging in pylsp:

    pylsp -v --log-file /tmp/pylsp.log

### Enabling tcp mode

Normally, editors communicate with language servers through standard
input/output. Optionally, you can run pylsp in tcp mode if you want to be able
to use the standard input/output, for example so you can use IPython or pudb,
using the --tcp flag:

    pylsp -v --log-file /tmp/pylsp.log --tcp --port 7090

Consult your lsp client documentation on how to connect to tcp-mode language
server, but if it doesn't support connecting to a language server via TCP, then
usually can configure `netcat`/`nc` to be your "language server" that will
proxy requests to a tcp-mode language server:

    nc localhost 7090

### Testing 

Run `tox` to run plugin tests.


## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) from 
[python-lsp/cookiecutter-pylsp-plugin](https://github.com/python-lsp/cookiecutter-pylsp-plugin)
project template.
