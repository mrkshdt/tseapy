import sys

import app as app_module
from app import app, create_app
from tseapy import __version__
from tseapy import cli


def test_version_is_single_sourced():
    assert isinstance(__version__, str)
    assert __version__


def test_app_uses_packaged_templates_and_static():
    assert app.template_folder is not None
    assert app.static_folder is not None
    assert app.template_folder.endswith("tseapy/templates")
    assert app.static_folder.endswith("tseapy/static")


def test_create_app_accepts_config_overrides():
    configured = create_app({"DEBUG": True, "MAX_CONTENT_LENGTH": 1234})
    assert configured.config["DEBUG"] is True
    assert configured.config["MAX_CONTENT_LENGTH"] == 1234


def test_cli_starts_app(monkeypatch):
    called = {}

    def fake_main(*, host, port, debug):
        called["host"] = host
        called["port"] = port
        called["debug"] = debug

    monkeypatch.setattr(app_module, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["tseapy", "--host", "0.0.0.0", "--port", "5055", "--debug"])

    exit_code = cli.main()
    assert exit_code == 0
    assert called == {"host": "0.0.0.0", "port": 5055, "debug": True}
