const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '../..');
const MOCK = path.join(ROOT, 'lib/capture/templates/claude-skills-mock.html');
const OUT  = path.join(ROOT, 'projects/claude-skills-guide/assets/screenshots');

fs.mkdirSync(OUT, { recursive: true });

const states = [
  { id: 'typing',    wait: 800  },
  { id: 'questions', wait: 5500 },
  { id: 'panel',     wait: 600  },
  { id: 'activate',  wait: 2500 }
];

(async () => {
  const browser = await chromium.launch({ headless: true });

  for (const s of states) {
    const page = await browser.newPage();
    await page.setViewportSize({ width: 540, height: 960 });
    const url = 'file:///' + MOCK.replace(/\\/g, '/') + '#' + s.id;
    await page.goto(url);
    await page.waitForTimeout(s.wait);
    const out = path.join(OUT, 'demo-' + s.id + '.png');
    await page.screenshot({ path: out });
    await page.close();
    console.log('captured: ' + out);
  }

  await browser.close();
  console.log('Done.');
})();
