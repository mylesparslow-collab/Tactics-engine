// Rasterize the drawn spell/equipment subjects (tools/cardkit/motifs/<id>.svg) to transparent 1024px PNGs for motif_art.py.
// node tools/cardkit/motif_raster.cjs <out_dir>
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const dir = path.join(__dirname, 'motifs');
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const ids = fs.readdirSync(dir).filter(f => f.endsWith('.svg')).map(f => f.slice(0, -4));
  for (const id of ids) {
    const svg = fs.readFileSync(path.join(dir, id + '.svg'), 'utf8');
    const b64 = await p.evaluate(async (src) => {
      const img = new Image(); img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(src); await img.decode();
      const c = document.createElement('canvas'); c.width = c.height = 1024;
      c.getContext('2d').drawImage(img, 0, 0, 1024, 1024);
      return c.toDataURL('image/png').split(',')[1];
    }, svg);
    fs.writeFileSync(path.join(out, id + '.png'), Buffer.from(b64, 'base64'));
  }
  console.log(`rasterized ${ids.length}`); await b.close();
})();
