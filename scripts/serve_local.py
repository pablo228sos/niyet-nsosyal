from __future__ import annotations

import argparse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.index import handler as ApiHandler  # noqa: E402
from api.experiment import handler as ExperimentHandler  # noqa: E402


class LocalHandler(SimpleHTTPRequestHandler):
    """Serve the checked-in web surface and the same API handler locally."""

    _json = ApiHandler._json

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/experiment"):
            ExperimentHandler.do_GET(self)
            return
        if self.path.rstrip("/") == "/api":
            ApiHandler.do_GET(self)
            return
        if self.path.rstrip("/") == "/lab":
            self.path = "/lab.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/api":
            self.send_error(404)
            return
        ApiHandler.do_POST(self)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalHandler)
    print(f"DRSK local demo: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
