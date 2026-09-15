from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "demo" / "nsosyal-overlay"
DIST = ROOT / "dist"
UNPACKED = DIST / "nsosyal-overlay"
ARCHIVE = DIST / "drsk-nsosyal-overlay.zip"
RUNTIME_FILES = (
    "manifest.json",
    "background.js",
    "content-v2.js",
    "overlay.css",
)


def validate_manifest() -> None:
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 3:
        raise SystemExit("overlay manifest must use Manifest V3")
    if manifest.get("host_permissions") != ["https://niyet-nsosyal.vercel.app/*"]:
        raise SystemExit("overlay host_permissions drifted from the fixed DRSK backend")
    content_script = manifest.get("content_scripts", [{}])[0]
    matches = content_script.get("matches", [])
    expected = ["https://nsosyal.com/*", "https://www.nsosyal.com/*"]
    if matches != expected:
        raise SystemExit("overlay content-script scope drifted from NSosyal")
    if content_script.get("js") != ["content-v2.js"]:
        raise SystemExit("overlay manifest must load the live composer adapter")


def write_deterministic_zip() -> None:
    if ARCHIVE.exists():
        ARCHIVE.unlink()

    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in RUNTIME_FILES:
            data = (SOURCE / name).read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def main() -> None:
    validate_manifest()
    missing = [name for name in RUNTIME_FILES if not (SOURCE / name).is_file()]
    if missing:
        raise SystemExit(f"missing overlay runtime files: {', '.join(missing)}")

    DIST.mkdir(parents=True, exist_ok=True)
    if UNPACKED.exists():
        shutil.rmtree(UNPACKED)
    UNPACKED.mkdir(parents=True)

    for name in RUNTIME_FILES:
        shutil.copy2(SOURCE / name, UNPACKED / name)

    write_deterministic_zip()
    print(f"Overlay package: {ARCHIVE.relative_to(ROOT)} ({ARCHIVE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
