from __future__ import annotations

import argparse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.experiment import handler as ExperimentHandler  # noqa: E402
from api.human_help import handler as HumanHelpHandler  # noqa: E402
from api.index import handler as ApiHandler  # noqa: E402


class LocalHandler(SimpleHTTPRequestHandler):
    """Serve the checked-in web surface and production API handlers locally.

    The local server is also the reliable multi-device demo target: every
    browser connected to this process sees the same HumanHelpService state.
    """

    _json = ApiHandler._json

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self) -> None:
        route = self.path.split("?", 1)[0].rstrip("/")
        if route == "/api":
            ApiHandler.do_GET(self)
            return
        if route == "/api/experiment":
            ExperimentHandler.do_GET(self)
            return
        if route == "/api/human-help":
            HumanHelpHandler.do_GET(self)
            return
        if route == "/lab":
            self.path = "/lab.html"
        if route in {"", "/live"}:
            self.path = "/live.html"
        super().do_GET()

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0].rstrip("/")
        if route == "/api":
            ApiHandler.do_POST(self)
            return
        if route == "/api/human-help":
            HumanHelpHandler.do_POST(self)
            return
        self.send_error(404)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address. Use 0.0.0.0 only on a trusted local network for multi-device demo.",
    )
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalHandler)
    print(f"DRSK local demo: http://{args.host}:{args.port}")
    if args.host == "0.0.0.0":
        print("Multi-device demo mode: connect devices to the same trusted LAN/hotspot and open this machine's LAN IP.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
