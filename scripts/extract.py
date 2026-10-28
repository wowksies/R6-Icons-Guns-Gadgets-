"""Extract textures from Rainbow Six Siege .forge archives.

Usage: py -3 extract.py <forge> <outdir> [--min-bytes N] [--max-bytes N]

Needs ooz.exe (Oodle Kraken decoder). Put it at ../ooz/ooz.exe or
point the OOZ_EXE environment variable at it.
"""
import csv
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import tex

OOZ_PATH = Path(os.environ.get("OOZ_EXE") or Path(__file__).resolve().parent.parent / "ooz" / "ooz.exe")
CONTAINER_MAGIC = bytes.fromhex("37aafb5799fa1510")
TEXTURE_TYPES = {0x9468B9E2, 0x05A61FAD, 0x13237FE9}


def iter_containers(data):
    off = 0
    while True:
        off = data.find(CONTAINER_MAGIC, off)
        if off < 0:
            return
        try:
            num = struct.unpack_from("<I", data, off + 15)[0]
            if num > 200000:
                off += 8
                continue
            cur = off + 19 + num * 8
            chunks = []
            total = 0
            ok = True
            for i in range(num):
                u, p = struct.unpack_from("<II", data, off + 19 + i * 8)
                if u < p or p > 256 * 1024 * 256:
                    ok = False
                    break
                cur += 4 + p
                chunks.append((u, p, cur - p))
                total += u
            if not ok or cur > len(data):
                off += 8
                continue
            yield off, cur, total, chunks
            off = cur
        except struct.error:
            off += 8


def decode_container(data, chunks, tmpdir):
    parts = []
    for u, p, data_off in chunks:
        blob = data[data_off:data_off + p]
        if u == p:
            parts.append(blob)
            continue
        inp = os.path.join(tmpdir, "c.ooz")
        out = os.path.join(tmpdir, "c.raw")
        with open(inp, "wb") as f:
            f.write(struct.pack("<Q", u))
            f.write(blob)
        subprocess.run([str(OOZ_PATH), "-f", "-d", inp, out],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(out, "rb") as f:
            parts.append(f.read())
    return b"".join(parts)


def parse_file_meta(payload):
    name_len, ctype = struct.unpack_from("<HH", payload, 0)
    if ctype != 2 or name_len > 4096 or 20 + name_len > len(payload):
        return None
    ftype, uid = struct.unpack_from("<IQ", payload, 8 + name_len)
    return {"name_len": name_len, "type": ftype, "uid": uid, "data_off": 20 + name_len}


def find_texture_trailer(payload, pixel_start):
    """Find the trailer whose surface size matches the block format exactly."""
    for do in range(max(pixel_start, len(payload) - 400), len(payload) - 47):
        sw = int.from_bytes(payload[do:do + 4], "little")
        sh = int.from_bytes(payload[do + 4:do + 8], "little")
        if sw == 0 or sh == 0 or sw > 16384 or sh > 16384:
            continue
        cs = int.from_bytes(payload[do + 16:do + 20], "little")
        if cs > 16:
            continue
        w, h = sw >> cs, sh >> cs
        if w <= 0 or h <= 0:
            continue
        fmt = int.from_bytes(payload[do + 32:do + 36], "little")
        ss = do - pixel_start
        if fmt == 0:
            if ss == w * h * 4:
                return do, w, h, fmt, cs
            continue
        info = tex.FORMATS.get(fmt)
        if info is None:
            continue
        block_size = info[1]
        blocks = ((w + 3) // 4) * ((h + 3) // 4)
        if ss == blocks * block_size or ss == tex.compressed_mip_chain_size(w, h, block_size):
            return do, w, h, fmt, cs
    return None


def extract_texture(payload):
    idx = payload.find(tex.TEXMAPDATA_MAGIC)
    if idx < 0:
        return None
    pixel_start = idx + 12
    found = find_texture_trailer(payload, pixel_start)
    if found is None:
        return None
    do, w, h, fmt, cs = found
    info = tex.FORMATS[fmt]
    blocks = ((w + 3) // 4) * ((h + 3) // 4)
    surface = payload[pixel_start:pixel_start + blocks * info[1]]
    if fmt == 0:
        from PIL import Image
        image = Image.frombytes("RGBA", (w, h), surface, "raw", "BGRA")
    else:
        import io
        from PIL import Image
        dds = tex._dds_dx10(w, h, surface, info[0])
        with Image.open(io.BytesIO(dds)) as src:
            image = src.convert("RGBA")
    texture_type = int.from_bytes(payload[do + 44:do + 48], "little")
    return image, w, h, fmt, texture_type, cs


def main():
    forge = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    min_bytes = 0
    max_bytes = 1 << 30
    args = sys.argv[3:]
    for i, a in enumerate(args):
        if a == "--min-bytes":
            min_bytes = int(args[i + 1])
        elif a == "--max-bytes":
            max_bytes = int(args[i + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    data = forge.read_bytes()
    rows = []
    containers = list(iter_containers(data))
    print(f"{forge.name}: {len(containers)} containers")
    with tempfile.TemporaryDirectory(dir=str(outdir)) as tmpdir:
        for n, (off, end, total, chunks) in enumerate(containers):
            if total < min_bytes or total > max_bytes:
                continue
            try:
                payload = decode_container(data, chunks, tmpdir)
            except Exception as e:
                print(f"  0x{off:x} decode failed: {e}")
                continue
            meta = parse_file_meta(payload)
            if meta is None or meta["type"] not in TEXTURE_TYPES:
                continue
            try:
                result = extract_texture(payload)
            except Exception as e:
                result = None
            if result is None:
                continue
            image, w, h, fmt, ttype, cs = result
            name = f"{forge.stem}_{off:08x}_{meta['uid']:012x}_{w}x{h}_f{fmt}_t{ttype}.png"
            image.save(outdir / name)
            rows.append({"forge": forge.name, "container": f"0x{off:x}", "uid": f"{meta['uid']:x}",
                         "width": w, "height": h, "format": fmt, "texture_type": ttype,
                         "png": name})
            if n % 50 == 0:
                print(f"  [{n}/{len(containers)}] {name}")
    with open(outdir / f"{forge.stem}_index.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["forge", "container", "uid", "width", "height", "format", "texture_type", "png"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"textures: {len(rows)} -> {outdir}")


if __name__ == "__main__":
    main()
