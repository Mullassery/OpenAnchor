"""Command-line entry point for ``python -m openanchor``.

Provides a minimal CLI so the package (and the Docker image built from
this repo) has a real, working entry point instead of crashing with
``No module named openanchor.__main__``.

Subcommands:
    version   Print the installed OpenAnchor version and exit.
    health    Print a JSON health/status summary and exit (used by the
              Docker HEALTHCHECK and for smoke-testing an install).
    serve     Start a tiny stdlib HTTP server exposing ``/health`` and
              ``/version`` endpoints. Useful as a container's foreground
              process so orchestrators (Docker/K8s) have something to
              probe. No third-party web framework required.

Running with no arguments prints usage and exits 0 (so ``docker run``
without extra args doesn't crash).
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import __version__


def _health_payload() -> dict:
    return {
        "status": "ok",
        "package": "openanchor",
        "version": __version__,
    }


class _HealthHandler(BaseHTTPRequestHandler):
    def _write_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming convention)
        if self.path in ("/health", "/healthz", "/"):
            self._write_json(_health_payload())
        elif self.path == "/version":
            self._write_json({"version": __version__})
        else:
            self._write_json({"error": "not found", "path": self.path}, status=404)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep container logs quiet by default; errors still surface via
        # exceptions. Silence the default per-request stderr logging.
        return


def _cmd_version(_args: argparse.Namespace) -> int:
    print(__version__)
    return 0


def _cmd_health(_args: argparse.Namespace) -> int:
    print(json.dumps(_health_payload()))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    server = HTTPServer((args.host, args.port), _HealthHandler)
    print(f"openanchor health server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openanchor",
        description=(
            "OpenAnchor: LLM token-attribution middleware. "
            "Run without a subcommand to see this message."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    version_p = subparsers.add_parser("version", help="Print the installed version")
    version_p.set_defaults(func=_cmd_version)

    health_p = subparsers.add_parser("health", help="Print a health status JSON blob")
    health_p.set_defaults(func=_cmd_health)

    serve_p = subparsers.add_parser(
        "serve", help="Run a minimal HTTP health server (container default)"
    )
    serve_p.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1; use 0.0.0.0 in containers)"
    )
    serve_p.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    serve_p.set_defaults(func=_cmd_serve)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
