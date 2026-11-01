// Frame-timing harness: node tools/perf.cjs [url]  (run `npx vite --port 5199` first)
const { chromium } = require('playwright');
(async () => {
  const url = process.argv[2] || 'http://localhost:5199/';
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  pg.on('pageerror', e => console.log('pageerror', e.message));
  await pg.goto(url); await pg.waitForFunction(() => window.ebbPlay);
  const mission = await pg.evaluate(() => Object.keys(window.__ids ?? {})[0] ?? null);
  await pg.evaluate(() => { const c = document.querySelector('[data-m]'); });
  // start the first campaign mission via content
  await pg.evaluate(async () => { const m = await import('/src/engine/bundled.ts'); const c = m.loadBundledContent(); window.ebbPlay(Object.values(c.campaigns)[0].missions[0].mission); });
  await pg.waitForFunction(() => window.ebb && window.ebb());
  await pg.waitForTimeout(2500);
  // frame sampler
  const measure = (name, act, ms = 1500) => pg.evaluate(async ([name, act, ms]) => {
    const ts = []; let on = true;
    const tick = t => { ts.push(t); if (on) requestAnimationFrame(tick); }; requestAnimationFrame(tick);
    const fn = new Function('s', 'return (async()=>{' + act + '})()');
    const t0 = performance.now(); await fn(window.ebb()); await new Promise(r => setTimeout(r, ms)); on = false;
    const d = ts.slice(1).map((t, i) => t - ts[i]).sort((a, b) => a - b);
    const sum = d.reduce((a, b) => a + b, 0);
    return { name, frames: d.length, avgMs: +(sum / d.length).toFixed(1), p95: +d[Math.floor(d.length * .95)].toFixed(1), worst: +d[d.length - 1].toFixed(1), fps: +(1000 * d.length / sum).toFixed(1) };
  }, [name, act, ms]);
  const out = [];
  out.push(await measure('idle', ''));
  out.push(await measure('hand toggle x4', `const t=document.querySelector('.htoggle'); for(let i=0;i<4;i++){t.click(); await new Promise(r=>setTimeout(r,350));}`, 500));
  out.push(await measure('wheel zoom', `const c=document.querySelector('canvas'); for(let i=0;i<20;i++){c.dispatchEvent(new WheelEvent('wheel',{deltaY:i<10?-120:120,clientX:640,clientY:300,bubbles:true,cancelable:true})); await new Promise(r=>setTimeout(r,40));}`, 600));
  out.push(await measure('pan (WASD held)', `s.renderer.setPanVelocity(1,0); await new Promise(r=>setTimeout(r,1000)); s.renderer.setPanVelocity(-1,0); await new Promise(r=>setTimeout(r,1000)); s.renderer.setPanVelocity(0,0);`, 300));
  out.push(await measure('AI turn (end turn)', `s.endTurn(); await new Promise(r=>setTimeout(r,6000));`, 500));
  console.table(out); await b.close();
})();
