// Rasterize generated placeholder cards (content/cards/<id>.svg) that have no painted .webp into
// content/cards/<id>.ph.webp. The game ships the .ph.webp, not the SVG: published artifacts only accept
// raster images. Re-run after regenerating placeholders: node tools/cardkit/raster_placeholders.cjs
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const dir = path.join(__dirname, '../../content/cards');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const ids = fs.readdirSync(dir).filter(f => f.endsWith('.svg')).map(f => f.slice(0, -4))
    .filter(id => !fs.existsSync(path.join(dir, id + '.webp')));
  for (const id of ids) {
    const svg = fs.readFileSync(path.join(dir, id + '.svg'), 'utf8');
    const b64 = await p.evaluate(async (src) => {
      const img = new Image(); img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(src); await img.decode();
      const c = document.createElement('canvas'); c.width = img.naturalWidth * 2; c.height = img.naturalHeight * 2;
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      return c.toDataURL('image/webp', 0.9).split(',')[1];
    }, svg);
    fs.writeFileSync(path.join(dir, id + '.ph.webp'), Buffer.from(b64, 'base64'));
  }
  console.log(`rasterized ${ids.length}`); await b.close();
})();
