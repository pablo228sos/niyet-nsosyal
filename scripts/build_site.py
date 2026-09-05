"""Package the existing Python-backed UI for Sites without rewriting its engines.

The Sites Worker serves the exact web assets and forwards only the two existing
API routes to the project's deployed Python backend. No cookies are forwarded.
"""
from pathlib import Path
import base64
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
FILES = ['index.html', 'lab.html', 'design-system.css', 'app.js', 'main.js', 'lab.js', 'theme.js']
FILES += [file.relative_to(WEB).as_posix() for file in sorted((WEB / 'assets/niyet').glob('*'))]
MIME = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
for name in ['app.js', 'main.js', 'lab.js', 'theme.js']:
    subprocess.run(['node', '--check', str(WEB / name)], check=True)
assets = {
    '/' + name: {'body': base64.b64encode((WEB / name).read_bytes()).decode(), 'type': MIME[Path(name).suffix]}
    for name in FILES
}
dist = ROOT / 'dist' / 'server'
dist.mkdir(parents=True, exist_ok=True)
source = (ROOT / 'scripts' / 'site_worker.mjs').read_text(encoding='utf-8')
(dist / 'index.js').write_text('const ASSETS = ' + json.dumps(assets, separators=(',', ':')) + ';\n' + source, encoding='utf-8')
(ROOT / 'dist' / 'package.json').write_text('{"type":"module"}\n', encoding='utf-8')
subprocess.run(['node', '--check', str(dist / 'index.js')], check=True)
print(f'Build passed: {len(FILES)} assets, {(dist / "index.js").stat().st_size:,} byte Worker')
