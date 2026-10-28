# References

Notes on what I used and what did not lead anywhere, so the next person does not repeat the dead ends.

## RainbowForge

https://github.com/parzivail/RainbowForge

A C# reader for Siege's `.forge` containers. Used for the container layout: the file header, the table of entries, and the chunking used by newer archives. Its name decoding routine (a byte-wise XOR keyed by the asset uid, type and offset) was the first thing I tried on the current build. It produced garbage for this version, so the icons are matched by uid and offset instead.

The container parsing itself was still the useful part. `scripts/forge_scan.js` and `scripts/fetch_container.js` are a JavaScript rewrite of the small slice needed here, because the tooling around the process dump is Node.

## ooz

https://github.com/powzix/ooz

Open source Kraken, Mermaid, LZNA and Bitknit decompressor. The UI textures sit inside chunked payloads with `8c 0c` chunk headers, which is Kraken. Build with `build.bat`, then call `ooz -d input output`.

Alternatives that did not work: OodleSharp needs the official DLL from a specific game version, and the chunked framing here is not a plain Oodle stream anyway. ooz handles the raw chunk fine.

## R6 Unpacker and RainbowForge extraction

Neither tool reads the current UI archive format end to end. They handle single mesh assets and older bundles, and both were checked against the extracted textures before I wrote my own parser. Worth reading if you need meshes; not useful for UI art on this build.

## Ubisoft operator pages

https://www.ubisoft.com/en-gb/game/rainbow-six/siege/game-info/operators

The weapon glyphs, names, class and slot all come from these pages. Each operator page embeds weapon blocks as plain HTML: the name in a `<p>`, the image right after it, then the weapon class. 78 operator pages gave 206 entries, which collapsed to 118 unique weapons after dedupe. That includes the four shields, which are not in this repo.

The images are hotlinked from `staticctf.ubisoft.com`. The copies in `guns/png/` are the source files, not resized.

## Map data (not in this repo)

Checked for a top-down radar texture and there is not one. The UI archives have aerial menu backgrounds and no floorplans. Each map's `_mod.forge` holds a large geometry payload and `_gidata.forge` holds a fully high entropy payload, and no public parser exists for either. If you are here for maps, the official Ubisoft blueprint packs are the practical route.

## Texture format note

The texture header on this build starts with a format code in the trailer. Code 16 is BC7 sRGB and covers most of the UI art. Missing that code in the format table is why a first pass silently dropped 4,412 of 5,737 texture assets in `datapc64_merged_playgo_bnk_guitextures1.forge`, including the entire modern 160px glyph set. That bug is what made the old icons look out of date.
