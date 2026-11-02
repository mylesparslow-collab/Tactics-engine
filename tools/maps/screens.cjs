// Map screenshots: node tools/maps/screens.cjs <outDir> [mapId...]   (run `npx vite --port 5199` first)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const out = process.argv[2] || 'map-screens';
  const ids = process.argv.slice(3);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1600, height: 1000 } });
  pg.on('pageerror', e => console.log('pageerror', e.message));
  await pg.goto('http://localhost:5199/');
  await pg.waitForFunction(() => window.ebbSkirmish);
  for (const id of ids) {
    await pg.evaluate(id => window.ebbSkirmish(id, 'salt_concord', 'hadal_court'), id);
    await pg.waitForFunction(() => window.brinewake && window.brinewake());
    await pg.waitForTimeout(4000);
    // Close any briefing/hand overlays so the board shows.
    await pg.evaluate(() => { document.querySelectorAll('.toast, .briefing, .modal').forEach(e => e.remove()); });
    // Whole board, then a closer look at the middle.
    await pg.evaluate(() => { const g = window.brinewake().game; window.brinewake().renderer.frameTile({ x: (g.width - 1) / 2, y: (g.height - 1) / 2 }, 1, 0); });
    await pg.waitForTimeout(1500);
    await pg.screenshot({ path: `${out}/${id}.png` });
    await pg.evaluate(() => { const g = window.brinewake().game; window.brinewake().renderer.frameTile({ x: (g.width - 1) / 2, y: (g.height - 1) / 2 }, 2.4, 0); });
    await pg.waitForTimeout(2500);
    await pg.screenshot({ path: `${out}/${id}_close.png` });
    console.log('shot', id);
  }
  await b.close();
})();
