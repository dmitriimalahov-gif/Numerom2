"""Pictures for the morning letter: the NumerOM logo and planet badges in the app's planet colours
(mobile/src/lib/vedicVisuals.js) as a lit sphere with the planet's symbol.

Mail apps show PNG, not SVG: the badges are drawn with Pillow; the logo SVG is rendered with macOS Quick Look,
whose white backdrop is then made transparent. Run with the backend environment:

    backend/.service-venv/bin/python scripts/render-email-images.py
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'backend/assets/email'
# key, colour, rim, symbol (Unicode astronomical signs; Rahu and Ketu are the lunar nodes ☊ ☋).
PLANETS = [('surya', '#f47758', '#c9654e', '☉'), ('chandra', '#ffffff', '#8aafa0', '☽'), ('guru', '#fa9418', '#b96b0e', '♃'),
           ('rahu', '#ba9669', '#92724d', '☊'), ('budha', '#bedfd0', '#719b89', '☿'), ('shukra', '#f8cbd3', '#ba8390', '♀'),
           ('ketu', '#bcbfc0', '#777f82', '☋'), ('shani', '#3867ad', '#3867ad', '♄'), ('mangal', '#f53f58', '#b92640', '♂')]
SIZE = 128
SYMBOLS = '/System/Library/Fonts/Apple Symbols.ttf'


def light(colour):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b > 170


def hex_rgb(colour):
    return tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def planet_badge(colour, rim, symbol):
    """A sphere lit from the upper left like the app's planets (Brand.tsx): highlight → colour → rim, drawn 4× and scaled."""
    big = SIZE * 4
    image = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    pixels, centre, radius = image.load(), big / 2, big / 2 - 8
    light_x, light_y, reach = big * .34, big * .30, big * .78
    highlight, body, edge = (0xf4, 0xff, 0xfa), hex_rgb(colour), hex_rgb(rim)
    for y in range(big):
        for x in range(big):
            if (x - centre) ** 2 + (y - centre) ** 2 > radius ** 2:
                continue
            t = min(1.0, ((x - light_x) ** 2 + (y - light_y) ** 2) ** .5 / reach)
            pixels[x, y] = mix(highlight, body, t / .5) + (255,) if t < .5 else mix(body, edge, (t - .5) / .5) + (255,)
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, big - 8, big - 8], outline=edge + (255,), width=12)
    font = ImageFont.truetype(SYMBOLS, int(big * .5))
    draw.text((centre, centre), symbol, font=font, anchor='mm', fill=hex_rgb('#183B62' if light(colour) else '#FFFFFF') + (255,))
    return image.resize((SIZE, SIZE), Image.LANCZOS)


def render(svg_text, folder, name, size):
    source = Path(folder) / f'{name}.svg'
    source.write_text(svg_text, encoding='utf-8')
    subprocess.run(['qlmanage', '-t', '-s', str(size), '-o', folder, str(source)], check=True, capture_output=True)
    return Image.open(f'{source}.png').convert('RGBA')


def white_to_alpha(image):
    """The logo has no closed shape: whiteness becomes transparency, keeping each colour as it looks on white."""
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, _ = pixels[x, y]
            alpha = max(255 - r, 255 - g, 255 - b)
            if alpha == 0:
                pixels[x, y] = (255, 255, 255, 0)
                continue
            scale = 255 / alpha
            pixels[x, y] = tuple(max(0, min(255, round(255 - (255 - c) * scale))) for c in (r, g, b)) + (alpha,)
    return image


def main():
    (OUT / 'planets').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        for key, colour, rim, symbol in PLANETS:
            planet_badge(colour, rim, symbol).save(OUT / 'planets' / f'{key}.png', optimize=True)
            print(key, 'ok')
        logo = white_to_alpha(render((ROOT / 'packages/brand/numerom-logo.svg').read_text(encoding='utf-8'), folder, 'logo', 640))
        logo = logo.crop(logo.getbbox())
        logo.thumbnail((320, 320), Image.LANCZOS)
        logo.save(OUT / 'numerom-logo.png', optimize=True)
        print('logo ok', logo.size)


if __name__ == '__main__':
    main()
