"""Export the current gadget/HUD glyph family as upright PNGs plus a sheet.

Usage: py -3 export_gadget_set.py <out_dir> <sheet.jpg> <size> <src_dir> [src_dir ...]
Deduplicates identical images across source archives by pixel hash.
"""
import csv
import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw

out_arg, sheet_arg, size_arg = sys.argv[1], sys.argv[2], sys.argv[3]
src_dirs = [Path(p) for p in sys.argv[4:]]
size = int(size_arg)

dst = Path(out_arg)
sheet_path = Path(sheet_arg)
dst.mkdir(parents=True, exist_ok=True)
for old in dst.glob("g*.png"):
    old.unlink()

candidates = []
for src in src_dirs:
    for csv_path in src.glob("*_icons.csv"):
        for r in csv.DictReader(open(csv_path, encoding="utf-8")):
            if int(r["width"]) == size and int(r["height"]) == size:
                candidates.append((src, r))

print("candidates:", len(candidates))

seen = {}
for src, r in candidates:
    im = Image.open(src / r["png"]).convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
    key = hashlib.sha1(im.tobytes()).hexdigest()
    if key in seen:
        continue
    seen[key] = (src, r, im)

rows = []
for i, (key, (src, r, im)) in enumerate(sorted(seen.items(), key=lambda kv: kv[1][1]["png"])):
    name = f"g{size}_{i:03d}_{r['uid']}.png"
    im.save(dst / name)
    rows.append({"index": i, "file": name, "uid": r["uid"], "size": size,
                 "container": r["container"], "source": str(src / r["png"])})

with open(dst / "index.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["index", "file", "uid", "size", "container", "source"])
    w.writeheader()
    w.writerows(rows)

cell = 176
cols = 10
nrows = (len(rows) + cols - 1) // cols
canvas = Image.new("RGB", (cols * cell, nrows * (cell + 16)), (18, 18, 18))
for r in rows:
    im = Image.open(dst / r["file"])
    im.thumbnail((cell - 12, cell - 12), Image.LANCZOS)
    x = (r["index"] % cols) * cell + (cell - im.width) // 2
    y = (r["index"] // cols) * (cell + 16) + (cell - im.height) // 2
    canvas.paste(im, (x, y), im)

draw = ImageDraw.Draw(canvas)
for r in rows:
    x = (r["index"] % cols) * cell
    y = (r["index"] // cols) * (cell + 16) + cell
    draw.text((x + 4, y), f'{r["index"]:03d}  {r["uid"][:8]}', fill=(160, 160, 160))

canvas.save(sheet_path, quality=90)
print("exported:", len(rows), "->", dst)
print("sheet:", sheet_path, canvas.size)
