// Scrape operator loadouts by category (Primary/Secondary Weapon only).
// Usage: node scrape_weapons.js <out-dir>
const fs = require('fs');
const path = require('path');

const BASE = 'https://www.ubisoft.com/en-gb/game/rainbow-six/siege/game-info';
const OUT = path.resolve(process.argv[2] || 'webref');
fs.mkdirSync(OUT, { recursive: true });
const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

async function get(url) {
  const r = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.text();
}

(async () => {
  const index = await get(`${BASE}/operators`);
  const slugs = [...new Set([...index.matchAll(/href="([^"]*operators\/[a-z0-9-]+)"/g)]
    .map((m) => m[1].split('/').pop()))];
  console.log('operators:', slugs.length);

  const weapons = new Map();
  const queue = [...slugs];
  await Promise.all(Array.from({ length: 6 }, async () => {
    while (queue.length) {
      const slug = queue.shift();
      try {
        const html = await get(`${BASE}/operators/${slug}`);
        // Split into loadout categories by their h2 titles.
        const parts = html.split(/operator__loadout__category__title/);
        for (const part of parts) {
          const title = (part.match(/data-innertext="([^"]+)"/) || [])[1] || '';
          if (!/weapon/i.test(title)) continue;
          const re = /operator__loadout__weapon"><p>([^<]+)<\/p><div class="media"><img src="([^"]+)"[^>]*\/>?<\/div><p>([^<]*)<\/p>/g;
          let m;
          while ((m = re.exec(part))) {
            const name = m[1].replace(/&quot;/g, '"').trim();
            const type = (m[3] || '').trim();
            if (!weapons.has(name)) weapons.set(name, { name, url: m[2], category: title, type, operators: new Set() });
            weapons.get(name).operators.add(slug);
          }
        }
      } catch (e) {
        console.log('FAIL', slug, e.message);
      }
    }
  }));

  console.log('unique weapons:', weapons.size);
  const rows = [];
  for (const [name, w] of [...weapons.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const file = path.join(OUT, `${slugify(name)}.png`);
    try {
      const res = await fetch(w.url, { headers: { 'user-agent': 'Mozilla/5.0' } });
      if (!res.ok) throw new Error(String(res.status));
      fs.writeFileSync(file, Buffer.from(await res.arrayBuffer()));
    } catch (e) {
      console.log('IMG FAIL', name, e.message);
    }
    rows.push({ name, category: w.category, type: w.type, file, source: w.url, operators: [...w.operators].join(';') });
  }
  fs.writeFileSync(path.join(OUT, 'weapons.json'), JSON.stringify(rows, null, 2));
  console.log('saved', rows.length);
})();
