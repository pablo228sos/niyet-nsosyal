from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo" / "nsosyal-overlay"
DIST = ROOT / "dist"
UNPACKED = DIST / "nsosyal-overlay"
ARCHIVE = DIST / "drsk-nsosyal-overlay.zip"
DEFAULT_BACKEND_ORIGIN = "https://niyet-nsosyal.vercel.app"
RUNTIME_FILES = (
    "manifest.json",
    "background.js",
    "content-v2.js",
    "overlay.css",
    "published-flow.css",
)


def _clean_backend_origin(value: str | None) -> str:
    origin = (value or DEFAULT_BACKEND_ORIGIN).strip().rstrip("/")
    parsed = urlparse(origin)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise SystemExit("DRSK overlay backend origin must be a bare https origin")
    return origin


def validate_manifest(manifest: dict) -> None:
    if manifest.get("manifest_version") != 3:
        raise SystemExit("overlay manifest must use Manifest V3")
    if manifest.get("host_permissions") != [f"{DEFAULT_BACKEND_ORIGIN}/*"]:
        raise SystemExit("overlay source manifest drifted from the fixed production backend")
    content_script = manifest.get("content_scripts", [{}])[0]
    matches = content_script.get("matches", [])
    expected = ["https://nsosyal.com/*", "https://www.nsosyal.com/*"]
    if matches != expected:
        raise SystemExit("overlay content-script scope drifted from NSosyal")
    if content_script.get("js") != ["content-v2.js"]:
        raise SystemExit("overlay manifest must load the live composer adapter")


def build_runtime_files(backend_origin: str) -> dict[str, bytes]:
    source_manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    validate_manifest(source_manifest)

    runtime: dict[str, bytes] = {
        name: (SOURCE / name).read_bytes() for name in RUNTIME_FILES
    }

    manifest = dict(source_manifest)
    manifest["host_permissions"] = [f"{backend_origin}/*"]
    runtime["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    for runtime_name in ("background.js", "content-v2.js"):
        text = runtime[runtime_name].decode("utf-8")
        if DEFAULT_BACKEND_ORIGIN not in text:
            raise SystemExit(f"overlay {runtime_name} backend origin is missing")
        runtime[runtime_name] = text.replace(
            DEFAULT_BACKEND_ORIGIN,
            backend_origin,
        ).encode("utf-8")
    return runtime


def write_deterministic_zip(runtime_files: dict[str, bytes]) -> None:
    if ARCHIVE.exists():
        ARCHIVE.unlink()

    with zipfile.ZipFile(
        ARCHIVE,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name in RUNTIME_FILES:
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, runtime_files[name])


def main() -> None:
    missing = [name for name in RUNTIME_FILES if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"missing overlay runtime files: {', '.join(missing)}")

    backend_origin = _clean_backend_origin(os.getenv("DRSK_OVERLAY_BACKEND_ORIGIN"))
    runtime_files = build_runtime_files(backend_origin)

    DIST.mkdir(parents=True, exist_ok=True)
    if UNPACKED.exists():
        shutil.rmtree(UNPACKED)
    UNPACKED.mkdir(parents=True)

    for name in RUNTIME_FILES:
        (UNPACKED / name).write_bytes(runtime_files[name])

    write_deterministic_zip(runtime_files)
    print(
        f"Overlay package: {ARCHIVE.relative_to(ROOT)} "
        f"({ARCHIVE.stat().st_size:,} bytes; backend={backend_origin})"
    )


if __name__ == "__main__":
    main()
