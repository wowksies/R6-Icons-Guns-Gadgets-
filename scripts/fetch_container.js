// Scratch: decode a container at an offset and save the payload.
// Usage: node fetch_container.js <forge> <offset-hex> <out> [ooz.exe]
// ooz.exe can also be set with the OOZ_EXE environment variable.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const [forgePath, offHex, outPath, oozArg] = process.argv.slice(2);
if (!forgePath || !offHex || !outPath) {
  console.error('usage: node fetch_container.js <forge> <offset-hex> <out> [ooz.exe]');
  process.exit(1);
}

const OOZ = oozArg || process.env.OOZ_EXE;
if (!OOZ) {
  console.error('ooz.exe not set: pass it as the fourth argument or set OOZ_EXE');
  process.exit(1);
}

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'r6forge-'));
const b = fs.readFileSync(forgePath);
const off = parseInt(offHex, 16);
const num = b.readUInt32LE(off + 15);
let cur = off + 19 + num * 8;
const parts = [];
for (let i = 0; i < num; i++) {
  const u = b.readUInt32LE(off + 19 + i * 8);
  const p = b.readUInt32LE(off + 19 + i * 8 + 4);
  const dataOff = cur + 4;
  cur = dataOff + p;
  if (u === p) { parts.push(b.subarray(dataOff, dataOff + p)); continue; }
  const hdr = Buffer.alloc(8); hdr.writeBigUInt64LE(BigInt(u));
  fs.writeFileSync(path.join(TMP, 'c.ooz'), Buffer.concat([hdr, b.subarray(dataOff, dataOff + p)]));
  execFileSync(OOZ, ['-f', '-d', path.join(TMP, 'c.ooz'), path.join(TMP, 'c.raw')], { stdio: 'pipe' });
  parts.push(fs.readFileSync(path.join(TMP, 'c.raw')));
}
fs.writeFileSync(outPath, Buffer.concat(parts));
fs.rmSync(TMP, { recursive: true, force: true });
console.log('saved', outPath, parts.reduce((a, x) => a + x.length, 0));
