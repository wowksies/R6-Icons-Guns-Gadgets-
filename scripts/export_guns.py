"""Export named gun icons (official Ubisoft loadout glyphs) with sheets and index.

Usage: py -3 export_guns.py <weapons-dir> <output-dir>

The weapons dir must contain weapons.json and the downloaded PNGs from
scrape_weapons.js.
"""
import csv
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

if len(sys.argv) < 3:
    sys.exit("usage: py -3 export_guns.py <weapons-dir> <output-dir>")
SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
GUNS = OUT / "guns"
SHIELDS = OUT / "shields"
WHITE = OUT / "white"
for d in (GUNS, SHIELDS, WHITE):
    d.mkdir(parents=True, exist_ok=True)
for p in list(GUNS.glob("*.png")) + list(SHIELDS.glob("*.png")) + list(WHITE.glob("*.png")):
    p.unlink()

ALIAS = {"9X19SVN": "9x19VSN"}  # same gun, transposed letters on one operator page


def safe(name: str) -> str:
    name = name.replace("&quot;", "").replace('"', "")
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    return re.sub(r"\s+", " ", name).strip()


rows = json.load(open(SRC / "weapons.json", encoding="utf-8"))

uniq = {}
for r in rows:
    name = ALIAS.get(r["name"].strip(), r["name"].strip())
    key = name.upper()
    if key in uniq:
        uniq[key]["operators"] += ";" + r["operators"]
        if not uniq[key].get("type") and r.get("type"):
            uniq[key]["type"] = r["type"]
        continue
    r = dict(r)
    r["name"] = name
    uniq[key] = r

out = []
for key, r in sorted(uniq.items()):
    name = safe(r["name"])
    try:
        im = Image.open(r["file"]).convert("RGBA")
    except Exception:
        continue
    is_shield = "SHIELD" in name.upper()
    folder = SHIELDS if is_shield else GUNS
    im.save(folder / f"{name}.png")
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(im.getchannel("A"))
    white.save(WHITE / f"{name}.png")
    out.append({"name": name, "kind": "shield" if is_shield else "firearm",
                "type": r.get("type", ""), "category": r["category"],
                "operators": r["operators"], "source": r["source"]})

with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "kind", "type", "category", "operators", "source"])
    w.writeheader()
    w.writerows(out)


def sheet(items, path, cols=5):
    cell_w, cell_h = 300, 96
    nrows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell_w, nrows * cell_h), (240, 240, 240))
    for i, r in enumerate(items):
        folder = SHIELDS if r["kind"] == "shield" else GUNS
        im = Image.open(folder / f"{r['name']}.png")
        im.thumbnail((cell_w - 20, cell_h - 40), Image.LANCZOS)
        x = (i % cols) * cell_w + (cell_w - im.width) // 2
        y = (i // cols) * cell_h + 8
        canvas.paste(im, (x, y), im)
    draw = ImageDraw.Draw(canvas)
    for i, r in enumerate(items):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h + cell_h - 20
        label = f"{r['name']}  ({r['type'] or r['category'].replace(' Weapon','')})"
        draw.text((x + 8, y), label[:46], fill=(20, 20, 20))
    canvas.save(path, quality=90)
    canvas.copy().resize((canvas.width // 2, canvas.height // 2)).save(
        path.with_name(path.stem + "_preview.jpg"), quality=86)
    print(path, canvas.size)


guns = [r for r in out if r["kind"] == "firearm"]
shields = [r for r in out if r["kind"] == "shield"]
sheet(guns, OUT / "_guns_sheet.jpg")
sheet(shields, OUT / "_shields_sheet.jpg", cols=4)
print("firearms", len(guns), "shields", len(shields))
