from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .config import AppConfig
from .fs42 import FS42Client
from .playlist import render_m3u, render_xmltv


class Fs42StreamHandler(BaseHTTPRequestHandler):
    config: AppConfig
    fs42: FS42Client

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._send(200, "text/plain", b"ok\n")
        elif path == "/live/fs42stream.m3u":
            self._send(200, "audio/x-mpegurl", render_m3u(self.config).encode())
        elif path == "/guide.xml":
            now = datetime.now(timezone.utc)
            try:
                blocks = self.fs42.schedule(now - timedelta(hours=1), now + timedelta(hours=12))
            except Exception:  # guide can be empty while live fallback handles outages
                blocks = []
            self._send(200, "application/xml", render_xmltv(self.config, blocks).encode())
        elif path == f"/live/{self.config.channel.station_name}.ts":
            message = (
                "live streaming supervisor is scaffolded; next step is wiring "
                "FFmpeg process output to this response with /runtime/brb.jpg fallback\n"
            )
            self._send(501, "text/plain", message.encode())
        else:
            self._send(404, "text/plain", b"not found\n")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_server(config: AppConfig) -> ThreadingHTTPServer:
    class ConfiguredHandler(Fs42StreamHandler):
        pass

    ConfiguredHandler.config = config
    ConfiguredHandler.fs42 = FS42Client(config)
    return ThreadingHTTPServer((config.bind_host, config.bind_port), ConfiguredHandler)


def main() -> None:
    config = AppConfig.from_env()
    server = build_server(config)
    print(f"fs42stream listening on http://{config.bind_host}:{config.bind_port}", flush=True)
    server.serve_forever()
