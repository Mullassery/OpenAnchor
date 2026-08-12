"""Tests for openanchor/__main__.py (Dockerfile's `python -m openanchor`
entry point, previously nonexistent -> CMD crashed immediately).
"""

import json
import threading
import urllib.request

from openanchor import __version__
from openanchor.__main__ import build_parser, main


class TestCliCommands:
    def test_no_args_prints_help_and_exits_zero(self, capsys):
        assert main([]) == 0
        captured = capsys.readouterr()
        assert "openanchor" in captured.out

    def test_version_command(self, capsys):
        assert main(["version"]) == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == __version__

    def test_health_command(self, capsys):
        assert main(["health"]) == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload["status"] == "ok"
        assert payload["version"] == __version__


class TestParser:
    def test_parser_has_serve_subcommand_with_host_port(self):
        parser = build_parser()
        args = parser.parse_args(["serve", "--host", "0.0.0.0", "--port", "9000"])
        assert args.host == "0.0.0.0"
        assert args.port == 9000

    def test_serve_default_host_is_loopback(self):
        parser = build_parser()
        args = parser.parse_args(["serve"])
        assert args.host == "127.0.0.1"
        assert args.port == 8080


class TestServeHttpServer:
    def test_health_endpoint_responds(self):
        from http.server import HTTPServer

        from openanchor.__main__ import _HealthHandler

        server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as resp:
                data = json.loads(resp.read())
                assert data["status"] == "ok"

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/version", timeout=5) as resp:
                data = json.loads(resp.read())
                assert data["version"] == __version__
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_unknown_path_returns_404(self):
        from http.server import HTTPServer
        from urllib.error import HTTPError

        from openanchor.__main__ import _HealthHandler

        server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/nope", timeout=5)
                assert False, "expected HTTPError"
            except HTTPError as e:
                assert e.code == 404
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
