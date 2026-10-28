// Scratch: scan Scimitar .forge archives for containers + chunk stats.
const fs = require('fs');

const magic = Buffer.from('37aafb5799fa1510', 'hex');
const files = process.argv.slice(2);

for (const f of files) {
  const b = fs.readFileSync(f);
  let off = 0, n = 0, comp = 0, raw = 0, bad = 0, totalUnpacked = 0, firstRaw = null;
  while ((off = b.indexOf(magic, off)) !== -1) {
    n++;
    try {
      const block = b.readUInt16LE(off + 8);
      const flag = b[off + 12];
      const desc = b.readUInt16LE(off + 13);
      const num = b.readUInt32LE(off + 15);
      if (num > 1000000) { bad++; off += 8; continue; }
      let cur = off + 19 + num * 8, ok = true, uc = 0, rc = 0;
      for (let i = 0; i < num; i++) {
        const u = b.readUInt32LE(off + 19 + i * 8);
        const p = b.readUInt32LE(off + 19 + i * 8 + 4);
        if (u < p) { ok = false; break; }
        cur += 4 + p;
        uc += u; rc += p;
        if (u > p) comp++; else raw++;
        if (u <= p && firstRaw === null) firstRaw = { at: cur - 4 - p, size: p };
      }
      if (!ok) { bad++; off += 8; continue; }
      totalUnpacked += uc;
      if (n <= 3) console.log(f, 'container@0x' + off.toString(16), 'block', block, 'flag', flag, 'desc', desc, 'chunks', num, 'unpacked', uc, 'packed', rc);
      off = cur;
    } catch (e) { bad++; off += 8; }
  }
  console.log('=>', f, 'containers', n, 'bad', bad, 'chunks comp', comp, 'raw', raw,
    'unpacked', (totalUnpacked / 1048576).toFixed(1) + 'MB', 'firstRaw', JSON.stringify(firstRaw));
}
