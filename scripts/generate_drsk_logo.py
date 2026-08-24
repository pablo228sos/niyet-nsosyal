"""Generate the compact DRSK landing mark as a deterministic WebP asset."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "assets" / "logo.webp"
SIZE = 256


def main() -> None:
    image = Image.new("RGB", (SIZE, SIZE), "#121524")
    pixels = image.load()
    for y in range(SIZE):
        for x in range(SIZE):
            mix = (x + y) / (2 * (SIZE - 1))
            pixels[x, y] = (
                round(18 + 42 * mix),
                round(21 + 31 * mix),
                round(36 + 107 * mix),
            )

    draw = ImageDraw.Draw(image)
    bars = ((58, 126, 78, 190), (92, 96, 112, 190), (126, 66, 146, 190), (160, 39, 180, 190))
    for index, bounds in enumerate(bars):
        color = (207 - index * 16, 248 - index * 6, 255)
        draw.rounded_rectangle(bounds, radius=10, fill=color)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "WEBP", quality=95, method=6)


if __name__ == "__main__":
    main()
