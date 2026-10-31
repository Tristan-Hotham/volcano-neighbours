// QA: open index.html at 1280 px and 390 px, collect console errors, take screenshots, exercise the controls.
const { chromium } = require('playwright');
const path = require('path');
const LF = process.env.LEAFLET_DIR || '/tmp/claude-0/qa/node_modules/leaflet/dist';  // local Leaflet 1.9.4 (the CDN is not reachable from the build container)
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const b = await chromium.launch();
  for (const [w, h, tag] of [[1280, 900, 'desktop'], [390, 844, 'phone']]) {
    for (const scheme of (tag === 'desktop' ? ['light', 'dark'] : ['light'])) {
      const p = await b.newPage({ viewport: { width: w, height: h }, colorScheme: scheme });
      const errs = [];
      p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
      await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
      await p.route(/leaflet.min.js/, r => r.fulfill({ path: LF + '/leaflet.js' }));
      await p.route(/leaflet.min.css/, r => r.fulfill({ path: LF + '/leaflet.css' }));
      await p.goto('file://' + ROOT + '/index.html', { waitUntil: 'load' });
      await p.waitForTimeout(1200);
      const t = scheme === 'dark' ? tag + '_dark' : tag;
      await p.screenshot({ path: `${ROOT}/qa/${t}_top.png` });
      await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
      await p.waitForTimeout(400);
      await p.screenshot({ path: `${ROOT}/qa/${t}_map_world.png` });
      if (scheme === 'dark') { await p.close(); console.log(t, 'errors', errs.filter(e => !/ERR_|net::|Failed to load resource/.test(e))); continue; }
      await p.evaluate(() => goVolcano(byName('Vesuvius'))); await p.waitForTimeout(900);
      await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
      await p.screenshot({ path: `${ROOT}/qa/${tag}_vesuvius.png` });
      await p.evaluate(() => { setRing(100); pickCountry('IDN', true); }); await p.waitForTimeout(500);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_indonesia_100.png` });
      await p.evaluate(() => { setRing(10); map.fitBounds(ZONES.java); }); await p.waitForTimeout(400);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_java_10.png` });
      await p.click('.lyrBtn'); await p.waitForTimeout(200);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_layers.png` });
      await p.click('.lyrBtn');
      await p.fill('#q', 'Popoc'); await p.waitForTimeout(200);
      const sug = await p.$eval('#sug', e => e.textContent);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_search.png` });
      await p.keyboard.press('Enter'); await p.waitForTimeout(600);
      const sel = await p.evaluate(() => S.sel && S.sel.n);
      for (const id of ['rangeChart', 'ctChart', 'topChart', 'recentChart', 'eclsChart', 'centChart', 'deadTab']) {
        await p.evaluate(id => document.getElementById(id).scrollIntoView({ block: 'center' }), id); await p.waitForTimeout(150);
        await p.screenshot({ path: `${ROOT}/qa/${tag}_${id}.png` });
      }
      const fs = await p.$$eval('.mfs-btn', e => e.length);
      await p.evaluate(() => document.getElementById('atlas').scrollIntoView());
      await p.click('.mfs-btn'); await p.waitForTimeout(500);
      await p.screenshot({ path: `${ROOT}/qa/${tag}_fullscreen.png` });
      const sw = await p.evaluate(() => document.documentElement.scrollWidth);
      console.log(tag, 'fullscreen buttons', fs, 'scrollWidth', sw, 'search:', sug.slice(0, 80), 'selected:', sel);
      console.log(tag, 'errors', errs.filter(e => !/ERR_|net::|Failed to load resource/.test(e)), 'network errors', errs.filter(e => /ERR_|net::|Failed to load resource/.test(e)).length);
      await p.close();
    }
  }
  await b.close();
})();
