"""Create bounded web derivatives of the supplied NIYET assets. Requires Pillow."""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'design/asset-pack/NIYET_UI_Assets_Pack'
OUT = ROOT / 'web/assets/niyet'
OUT.mkdir(parents=True, exist_ok=True)
for original, target, width in [
    ('backgrounds/bg-02-focus.jpg', 'focus.webp', 900),
    ('hero/hero-wave-01.png', 'wave.webp', 760),
    ('hero/hero-wave-01.png', 'wave-small.webp', 380),
    ('gradients/gradient-04.png', 'lab-glow.webp', 480),
    ('patterns/pattern-grid.png', 'grid.webp', 512),
    ('patterns/pattern-dots.png', 'dots.webp', 256),
]:
    image = Image.open(SOURCE / original)
    image.thumbnail((width, width))
    image.save(OUT / target, 'WEBP', quality=78, method=6)
    print(target, (OUT / target).stat().st_size)
for name in ['niyet-mark.svg', 'niyet-wordmark.svg']:
    shutil.copyfile(SOURCE / 'brand' / name, OUT / name)
symbols = []
for file in sorted((SOURCE / 'icons').glob('*.svg')):
    element = ET.fromstring(file.read_text())
    attrs = ' '.join(f'{key}="{value}"' for key, value in element.attrib.items() if key not in ['width', 'height'])
    children = ''.join(ET.tostring(child, encoding='unicode') for child in element)
    symbols.append(f'<symbol id="{file.stem}" {attrs}>{children}</symbol>')
(OUT / 'icons.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg">' + ''.join(symbols) + '</svg>', encoding='utf-8')
