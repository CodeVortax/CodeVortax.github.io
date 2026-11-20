#!/usr/bin/env python3
"""Render the link-preview images used by Telegram, WhatsApp, X and friends.

    python3 make_og.py

Writes:
  og/cover.png             1200x630, the site card
  og/<slug>.png            1200x630, one card per project

The typeface is Baloo 2, the same brand font the Focus app uses
(app/src/main/res/font/baloo2_variable.ttf, SIL OFL 1.1).

Telegram and WhatsApp crop 1200x630 down to roughly a square, so all the
important text stays inside the centre 630x630 area.
"""

import json
import pathlib
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data" / "projects"
OUT = ROOT / "og"
FONT_DIR = ROOT / "assets" / "fonts"
FONT_FILE = FONT_DIR / "Baloo2.ttf"
FONT_URL = ("https://raw.githubusercontent.com/CodeVortax/focus/main/"
            "app/src/main/res/font/baloo2_variable.ttf")

W, H = 1200, 630
BG = (11, 15, 23)
FG = (233, 238, 246)
MUTED = (155, 170, 190)
BLUE = (88, 166, 255)
VIOLET = (167, 139, 250)


def ensure_font():
    """Fetch the brand font once and keep it in assets/fonts."""
    if FONT_FILE.exists() and FONT_FILE.stat().st_size > 100_000:
        return FONT_FILE
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"downloading {FONT_FILE.name} ...")
    subprocess.run(
        ["curl", "-fsSL", "--retry", "3", "--retry-delay", "2",
         "--max-time", "120", "-o", str(FONT_FILE), FONT_URL],
        check=True,
    )
    return FONT_FILE


def font(size, weight=800):
    f = ImageFont.truetype(str(FONT_FILE), size)
    # Baloo 2 ships as a variable font; freeze the weight we want.
    try:
        f.set_variation_by_name(weight_names(weight))
    except Exception:
        pass
    return f


def weight_names(weight):
    table = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}
    return table.get(weight, "ExtraBold")


def gradient_bg():
    """Dark base with a blue and a violet glow, like the site."""
    img = Image.new("RGB", (W, H), BG)

    def glow(cx, cy, r, colour, alpha):
        layer = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)
        layer = layer.filter(ImageFilter.GaussianBlur(r // 2))
        return layer, alpha

    blue_layer, a1 = glow(250, 60, 420, (20, 80, 190), 1)
    violet_layer, a2 = glow(1000, 560, 380, (70, 40, 160), 1)
    img = Image.blend(img, Image.blend(img, blue_layer, 0.45), 0.55)
    img = Image.blend(img, violet_layer, 0.35)

    # faint grid, matching the hero background
    d = ImageDraw.Draw(img, "RGBA")
    step = 60
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(88, 166, 255, 12), width=1)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=(88, 166, 255, 12), width=1)

    # vignette so the edges stay dark
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-W // 3, -H // 3, W + W // 3, H + H // 3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGB", (W, H), BG)
    img = Image.composite(img, dark, mask)
    return img


def fit_font(draw, text, max_w, start, weight=800, floor=28):
    """Shrink the size until the text fits the width."""
    size = start
    while size > floor:
        f = font(size, weight)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(floor, weight)


def tracked(draw, xy, text, f, fill, spacing=0):
    """Draw text with letter spacing (PIL has none)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + spacing
    return x


def wrap(draw, text, f, max_w):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=f) <= max_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def brand_mark(draw, x, y, size=44, colour=BLUE):
    """The little '</>' that sits next to the wordmark."""
    w = max(4, size // 9)
    draw.line([(x + size * 0.38, y), (x + size * 0.06, y + size / 2),
               (x + size * 0.38, y + size)], fill=colour, width=w, joint="curve")
    draw.line([(x + size * 0.72, y), (x + size, y + size / 2),
               (x + size * 0.72, y + size)], fill=colour, width=w, joint="curve")


def base_card():
    img = gradient_bg()
    draw = ImageDraw.Draw(img)

    # brand row, top left
    brand_mark(draw, 84, 60, 40)
    f_brand = font(38, 700)
    draw.text((84 + 62, 52), "CodeVortax", font=f_brand, fill=FG)

    # hairline along the bottom edge
    draw.rectangle([0, H - 6, W, H], fill=BLUE)
    return img, draw


def cover_card():
    img, draw = base_card()

    f_kicker = font(23, 600)
    drawer = ImageDraw.Draw(img)
    kicker = "OPEN SOURCE  ·  ANDROID  ·  ESP32  ·  PYTHON"
    kw = drawer.textlength(kicker, font=f_kicker) + len(kicker) * 2
    # pill behind the kicker
    py = 176
    draw.rounded_rectangle([84, py, 84 + kw + 34, py + 46], radius=23,
                           outline=(40, 52, 70), width=2, fill=(18, 24, 34))
    draw.ellipse([84 + 18, py + 18, 84 + 28, py + 28], fill=(63, 185, 80))
    tracked(draw, (84 + 42, py + 9), kicker, f_kicker, MUTED, spacing=2)

    # headline
    f_h1 = font(112, 800)
    draw.text((80, 246), "CodeVortax", font=f_h1, fill=FG)

    # subtitle, wrapped to the centre-safe width
    f_sub = font(38, 500)
    sub = "Android apps, ESP32 firmware and sharp little CLI tools."
    lines = wrap(draw, sub, f_sub, 900)
    y = 396
    for line in lines:
        draw.text((84, y), line, font=f_sub, fill=MUTED)
        y += 48

    # url
    f_url = font(28, 600)
    draw.text((84, H - 96), "codevortax.github.io", font=f_url, fill=BLUE)
    return img


def project_card(p):
    img, draw = base_card()

    # kicker: category + language
    cat = {"android": "ANDROID", "esp32": "ESP32 FIRMWARE",
           "tool": "CLI & TOOLS", "web": "WEB TOOL"}[p["cat"]]
    f_kicker = font(22, 600)
    kicker = f"{cat}  ·  {p['lang'].upper()}"
    kw = draw.textlength(kicker, font=f_kicker) + len(kicker) * 2
    py = 168
    draw.rounded_rectangle([84, py, 84 + kw + 34, py + 44], radius=22,
                           outline=(40, 52, 70), width=2, fill=(18, 24, 34))

    # colour dot in the project's language colour
    dot = p["color"].lstrip("#")
    try:
        dot_rgb = tuple(int(dot[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        dot_rgb = BLUE
    draw.ellipse([84 + 17, py + 17, 84 + 27, py + 27], fill=dot_rgb)
    tracked(draw, (84 + 40, py + 8), kicker, f_kicker, MUTED, spacing=2)

    # project name, shrunk to fit
    f_name = fit_font(draw, p["name"], 1000, 96, 800, 40)
    draw.text((80, 232), p["name"], font=f_name, fill=FG)

    # tagline
    f_tag = font(36, 500)
    import re
    tag = re.sub(r"<[^>]+>", "", p["tagline"])
    import html as html_mod
    tag = html_mod.unescape(tag)
    lines = wrap(draw, tag, f_tag, 880)[:3]
    y = 232 + f_name.size + 34
    for line in lines:
        draw.text((84, y), line, font=f_tag, fill=MUTED)
        y += 46

    # footer: licence and stars on the left, url on the right
    f_meta = font(26, 600)
    draw.text((84, H - 92), f"{p['license']}   ·   ★ {p['stars']}", font=f_meta, fill=MUTED)
    f_url = font(26, 600)
    drawn = draw.textlength("codevortax.github.io", font=f_url)
    draw.text((W - 84 - drawn, H - 92), "codevortax.github.io", font=f_url, fill=BLUE)
    return img


def main():
    ensure_font()
    OUT.mkdir(exist_ok=True)

    cover_card().save(OUT / "cover.png", optimize=True)

    projects = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(DATA.glob("*.json"))]
    for p in sorted(projects, key=lambda x: x["order"]):
        project_card(p).save(OUT / f"{p['slug']}.png", optimize=True)

    total = 1 + len(projects)
    print(f"wrote {total} images to og/")


if __name__ == "__main__":
    main()
