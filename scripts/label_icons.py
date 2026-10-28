"""Build a labelled icon folder from the current 160px set.

Usage: py -3 label_icons.py <extracted-dir> <output-dir>

The extracted dir must contain index.csv and the g*.png files from
export_gadget_set.py. Names are shape/function descriptions: the build stores
only hashed asset names, so no official operator/gadget naming is recoverable
from the install.
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw

NAMES = {
    0: ("armor-vest", "high", "plate carrier / body armour"),
    1: ("barbed-wire", "high", "razor wire coil"),
    2: ("barricade", "high", "wooden barricade planks"),
    3: ("camera-box", "medium", "boxy device with lens"),
    4: ("camera-dome", "high", "dome CCTV camera"),
    5: ("camera-tripod", "high", "camera on tripod"),
    6: ("grenade-handle", "medium", "round grenade with handle"),
    7: ("panel-circle", "medium", "square panel with round window"),
    8: ("canister-round", "medium", "round canister with straps"),
    9: ("charge-strap", "medium", "stick charge with straps"),
    10: ("drone-frame", "high", "three-arm drone chassis"),
    11: ("rappel", "high", "operator rappelling"),
    12: ("shield-slab", "medium", "deployable shield slab"),
    13: ("device-lever", "medium", "wall device with lever"),
    14: ("charge-diamond", "medium", "charge with diamond markings"),
    15: ("reinforcement-stack", "medium", "stacked reinforcement panels"),
    16: ("operator-outline", "medium", "operator silhouette"),
    17: ("planet", "low", "ringed planet"),
    18: ("spectre", "low", "ghost / spectre"),
    19: ("hat-device", "low", "cowboy hat over device"),
    20: ("helmet-winged", "medium", "winged helmet"),
    21: ("circle-dashed", "low", "dashed circle"),
    22: ("particles", "low", "particle burst"),
    23: ("flash", "low", "bright flash"),
    24: ("photo-map", "medium", "polaroid map photo"),
    25: ("six-logo", "high", "Rainbow Six logo"),
    26: ("diamond-dashed", "low", "dashed diamond"),
    27: ("glyph-k", "low", "font glyph K"),
    28: ("glyph-skip", "low", "font glyph >|"),
    29: ("dashes", "low", "dash marks"),
    30: ("helicopter", "high", "helicopter"),
    31: ("drone", "high", "drone, twin lens"),
    32: ("drone-alt", "high", "drone, bar lens"),
    33: ("drone-front", "high", "drone front view"),
    34: ("drone-front-alt", "high", "drone front view, bar"),
    35: ("drone-jammed", "high", "drone with X (jammed)"),
    36: ("drone-jammed-alt", "high", "drone with X (jammed)"),
    37: ("drone-glasses", "medium", "drone with goggles"),
    38: ("drone-glasses-alt", "medium", "drone with goggles"),
    39: ("panel-blank", "low", "blank rounded square"),
    40: ("circle-broken", "low", "broken dashed circle"),
    41: ("flashbang", "high", "flash grenade with burst"),
    42: ("reticle", "high", "targeting reticle"),
    43: ("device-toothed", "medium", "toothed device panel"),
    44: ("camera-grip", "medium", "handheld camera"),
    45: ("eye-scan", "high", "eye with circuit"),
    46: ("laptop-heart", "medium", "laptop with heart"),
    47: ("eye", "high", "eye"),
    48: ("shield-spark", "medium", "shield with spark"),
    49: ("syringe", "high", "syringe with cross"),
    50: ("grid-panel", "medium", "grid / ladder panel"),
    51: ("syringe-burst", "high", "syringe with burst"),
    52: ("bracket-spark", "medium", "bracket with spark"),
    53: ("spiked-hub", "medium", "spiked hub"),
    54: ("battery", "high", "battery with lightning"),
    55: ("pot-lightning", "medium", "pot with lightning"),
    56: ("antenna", "high", "antenna emitting waves"),
    57: ("briefcase-defuser", "high", "briefcase / defuser"),
    58: ("smoke-skull", "high", "smoke cloud with skull"),
    59: ("sledgehammer", "high", "sledgehammer with burst"),
    60: ("device-tripod", "medium", "three-arm device"),
    61: ("spike-cluster", "medium", "spike cluster"),
    62: ("capsules", "low", "two capsules"),
    63: ("flame", "high", "flame with triangle"),
    64: ("mine-quad", "medium", "square mine, four charges"),
    65: ("alert", "high", "exclamation alert"),
    66: ("hazard-stripes", "medium", "hazard-striped panel"),
    67: ("starburst", "low", "starburst with crosses"),
    68: ("shuriken", "medium", "star blade"),
    69: ("skull-syringe", "medium", "skull with syringes"),
    70: ("phone-signal", "high", "phone with signal rings"),
    71: ("arrows-cycle", "low", "circular arrows"),
    72: ("grenade-spiked", "medium", "spiked grenade"),
    73: ("target-x", "medium", "target with X"),
    74: ("stim-heart", "high", "heart with cross (stim)"),
    75: ("grave-eye", "medium", "grave with eye"),
    76: ("stim-pistol", "high", "syringe pistol"),
    77: ("goggles", "high", "goggles with lenses"),
    78: ("gear-eye", "medium", "gear with eye"),
    79: ("pickaxe", "high", "pickaxe / breach tool"),
    80: ("canister-flame", "high", "canister with flame"),
    81: ("bearing", "medium", "bearing / gear ring"),
    82: ("crosshair-spark", "medium", "crosshair with sparks"),
    83: ("blade-face", "low", "split face / blade"),
    84: ("punch", "high", "punching fist"),
    85: ("triangle-device", "medium", "triangle device with waves"),
    86: ("baton-cross", "medium", "crossed batons"),
    87: ("armor-carrier", "high", "armour plate carrier"),
    88: ("plates-stack", "medium", "stacked plates"),
    89: ("cloud-arrow", "low", "cloud with arrow"),
    90: ("star-wand", "low", "star and wand"),
    91: ("arrow-wing", "low", "winged arrow"),
    92: ("binoculars", "high", "binoculars"),
    93: ("turret", "medium", "turret on base"),
    94: ("circle-dots", "low", "ring with dots"),
    95: ("darts", "medium", "four darts"),
    96: ("ring-spiked", "medium", "spiked ring"),
    97: ("tank", "medium", "small tracked vehicle"),
    98: ("wall-breach", "medium", "wall with breach X"),
    99: ("crystal-canister", "medium", "crystal with canister"),
    100: ("tri-drones", "medium", "triangle of drones"),
    101: ("bomb-fuse", "high", "bomb with fuse"),
    102: ("fan", "medium", "fan blades"),
    103: ("crate-x", "medium", "crate with X"),
    104: ("stretcher", "high", "stretcher with cross"),
    105: ("pouch", "medium", "grenade pouch"),
    106: ("eye-slash", "medium", "slashed eye"),
    107: ("pods", "medium", "cluster of pods"),
    108: ("drone-bomber", "medium", "drone carrying charges"),
    109: ("sickle-dagger", "medium", "sickle and dagger"),
    110: ("camera-winged", "medium", "winged camera"),
    111: ("beetle", "medium", "beetle-shaped mine"),
    112: ("staff-trophy", "low", "staff with orbs"),
    113: ("knife-spikes", "medium", "knife with spikes"),
    114: ("dagger-flame", "medium", "flaming dagger"),
    115: ("dagger-rays", "medium", "dagger with rays"),
    116: ("brain-dagger", "high", "brain with dagger (interrogation)"),
    117: ("dagger-arcs", "medium", "dagger with arcs"),
    118: ("drone-camera", "high", "drone with camera"),
    119: ("rappel-kick", "high", "rappel entry kick"),
    120: ("sprint", "high", "sprinting operator"),
    121: ("visor", "medium", "visor / goggles"),
    122: ("snowflake", "medium", "snowflake"),
    123: ("bear-spiky", "low", "spiky bear"),
    124: ("bear-glasses", "low", "bear with glasses"),
    125: ("bear", "low", "fluffy bear"),
    126: ("tank-vehicle", "medium", "tracked vehicle"),
    127: ("robot", "medium", "robot with fragments"),
    128: ("skull-shield", "medium", "skull in shield"),
    129: ("phone-skull", "medium", "phone with skull"),
    130: ("dagger-drones", "low", "dagger with small drones"),
    131: ("orb-staff", "low", "spiked orb staff"),
    132: ("shield-lightning", "medium", "shield with lightning"),
    133: ("wall-grid", "medium", "panel with grid"),
    134: ("syrette-drones", "low", "syrette with drones"),
    135: ("lightning-block", "low", "blocky lightning"),
    136: ("device-screen", "medium", "device with screen"),
    137: ("phone-burst", "medium", "phone with burst"),
    138: ("fan-tri", "medium", "three-blade rotor"),
}

if len(sys.argv) < 3:
    sys.exit("usage: py -3 label_icons.py <extracted-dir> <output-dir>")
src = Path(sys.argv[1])
dst = Path(sys.argv[2])
black = dst / "black"
dst.mkdir(parents=True, exist_ok=True)
black.mkdir(parents=True, exist_ok=True)
for old in dst.glob("*.png"):
    old.unlink()
for old in black.glob("*.png"):
    old.unlink()

rows = list(csv.DictReader(open(src / "index.csv", encoding="utf-8")))
out = []
for r in rows:
    idx = int(r["index"])
    name, conf, note = NAMES.get(idx, (f"unidentified-{idx:03d}", "low", ""))
    filename = f"{idx:03d}_{name}.png"
    im = Image.open(src / r["file"]).convert("RGBA")
    im.save(dst / filename)
    a = im.getchannel("A")
    blk = Image.new("RGBA", im.size, (17, 17, 17, 255))
    blk.putalpha(a)
    blk.save(black / filename)
    out.append({"index": idx, "file": filename, "name": name, "confidence": conf,
                "notes": note, "uid": r["uid"], "source": r["source"]})

with open(dst / "names.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["index", "file", "name", "confidence", "notes", "uid", "source"])
    w.writeheader()
    w.writerows(out)

cell_w, cell_h = 176, 200
cols = 8
nrows = (len(out) + cols - 1) // cols
canvas = Image.new("RGB", (cols * cell_w, nrows * cell_h), (18, 18, 18))
for r in out:
    im = Image.open(dst / r["file"])
    im.thumbnail((cell_w - 16, cell_w - 16), Image.LANCZOS)
    x = (r["index"] % cols) * cell_w + (cell_w - im.width) // 2
    y = (r["index"] // cols) * cell_h + (cell_w - 16 - im.height) // 2 + 4
    canvas.paste(im, (x, y), im)

draw = ImageDraw.Draw(canvas)
for r in out:
    x = (r["index"] % cols) * cell_w
    y = (r["index"] // cols) * cell_h + cell_w - 4
    draw.text((x + 5, y), f'{r["index"]:03d} {r["name"][:24]}', fill=(170, 170, 170))
canvas.save(dst / "_sheet_labelled.jpg", quality=90)
canvas.copy().resize((canvas.width // 2, canvas.height // 2)).save(dst / "_sheet_labelled_preview.jpg", quality=86)
print("labelled", len(out), "->", dst, canvas.size)
