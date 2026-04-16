#!/usr/bin/env node
/**
 * capture-github-scroll.js
 *
 * Takes a TALL full-page screenshot of a GitHub README at a narrow (540px)
 * portrait viewport — produces an image GuidedDemo can y-pan through to
 * simulate smooth vertical scrolling through the skills list.
 *
 * Why narrow viewport?
 *   Wide screenshots (2560×1340) are landscape. GuidedDemo cover-scales to
 *   fill the 1080×1728 container → dispH ≈ contentH → zero y-pan room.
 *   At 540px wide: coverScale = max(1080/540, 1728/H) = 2.0 (width wins),
 *   dispW = 1080 (exact), dispH = H×2. For H=4000 → dispH=8000, giving
 *   4272px of vertical scroll travel (52% of the image height).
 *
 * Also finds skill row y-positions in the DOM and prints ready-to-paste
 * highlight_moments JSON so you can add orange highlight boxes that track
 * each skill as the camera scrolls past it.
 *
 * Usage:
 *   node lib/capture/capture-github-scroll.js \
 *     --url https://github.com/coreyhaines31/marketingskills/blob/main/README.md \
 *     --out remotion/public/demo-frames/github-readme-scroll.png \
 *     --skills "content-strategy,copywriting,campaign-planning,ad-creator,humanizer"
 *
 * After running:
 *   1. Note the image height printed to console.
 *   2. Use the highlight_moments JSON printed at the end.
 *   3. Update beat-keywords-bg in timeline.json (template below).
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

function parseArgs() {
  const a = process.argv.slice(2);
  const out = {
    url: 'https://github.com/coreyhaines31/marketingskills/blob/main/README.md',
    skills: 'content-strategy,copywriting,campaign-planning,ad-creator,humanizer',
    viewportW: 540,
  };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--url')         out.url       = a[++i];
    else if (a[i] === '--out')    out.out       = a[++i];
    else if (a[i] === '--skills') out.skills    = a[++i];
    else if (a[i] === '--viewport-w') out.viewportW = parseInt(a[++i], 10);
  }
  if (!out.out) out.out = 'remotion/public/demo-frames/github-readme-scroll.png';
  out.skillList = out.skills.split(',').map(s => s.trim().toLowerCase());
  return out;
}

async function main() {
  const args = parseArgs();

  console.log('→ launching browser');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: args.viewportW, height: 900 },
    deviceScaleFactor: 1,
    // Neutral UA to avoid GitHub serving a degraded page
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  console.log(`→ loading ${args.url}`);
  await page.goto(args.url, { waitUntil: 'networkidle', timeout: 45000 });
  // Extra settle for GitHub's JS rendering
  await page.waitForTimeout(2500);

  // Pre-scroll to force lazy-load images and table content
  const initialH = await page.evaluate(() => document.documentElement.scrollHeight);
  console.log(`→ pre-scroll pass (page height: ${initialH}px)`);
  for (let y = 0; y <= initialH; y += 300) {
    await page.evaluate((sy) => window.scrollTo(0, sy), y);
    await page.waitForTimeout(40);
  }
  await page.waitForTimeout(1500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(800);

  // Final full page height after lazy content rendered
  const fullH = await page.evaluate(() => document.documentElement.scrollHeight);
  console.log(`→ final page height: ${fullH}px at ${args.viewportW}px viewport`);

  // ── Find skill row DOM positions ──────────────────────────────────────────
  const skillPositions = {};

  for (const skill of args.skillList) {
    const pos = await page.evaluate((skillName) => {
      // GitHub renders README tables as <table> with <td>/<th> cells.
      // The skill name is typically in the first cell of each row.
      const cells = document.querySelectorAll('table td:first-child, table th:first-child');
      for (const cell of cells) {
        const text = cell.textContent.trim().toLowerCase();
        if (text === skillName || text.startsWith(skillName)) {
          const rect = cell.getBoundingClientRect();
          const scrollTop = window.scrollY;
          return { top: rect.top + scrollTop, height: rect.height };
        }
      }
      // Fallback: search all elements for exact text match
      const all = document.querySelectorAll('td, th, li, a, code, span');
      for (const el of all) {
        if (el.textContent.trim().toLowerCase() === skillName) {
          const rect = el.getBoundingClientRect();
          return { top: rect.top + window.scrollY, height: rect.height };
        }
      }
      return null;
    }, skill);

    if (pos) {
      const yPct  = parseFloat(((pos.top  / fullH) * 100).toFixed(2));
      const hPct  = parseFloat(((pos.height / fullH) * 100).toFixed(2));
      const hPctMin = Math.max(1.5, hPct); // never less than 1.5%
      skillPositions[skill] = { topPx: pos.top, yPct, hPct: hPctMin };
      console.log(`  ✓ "${skill}" found at y=${pos.top}px (${yPct}% of ${fullH}px)`);
    } else {
      console.log(`  ⚠ "${skill}" NOT found in DOM — check skill name spelling`);
    }
  }

  // ── Take full-page screenshot ─────────────────────────────────────────────
  fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
  console.log(`→ screenshotting full page → ${args.out}`);
  await page.screenshot({ path: args.out, fullPage: true });
  await browser.close();

  const sizeMB = (fs.statSync(args.out).size / 1024 / 1024).toFixed(2);
  console.log(`✓ saved ${args.out} (${sizeMB} MB, ${args.viewportW}×${fullH}px)`);

  // ── Compute GuidedDemo y-pan to reach each skill at the right moment ──────
  //
  // GuidedDemo math for a 540×H image in 1080×1728 container:
  //   coverScale  = 2.0 (width wins: 1080/540)
  //   dispH       = H × 2.0
  //   maxScrollPx = dispH - 1728
  //   panY=0  → top of image visible; panY=100 → bottom of image visible
  //
  // To show a skill row (at image px topPx) centered on screen:
  //   wantDispY  = topPx × 2.0  (convert image px to display px)
  //   panOffsetY = wantDispY - 1728/2  (center the row in the 1728px container)
  //   panY       = panOffsetY / maxScrollPx × 100
  //
  // The keyword beat runs 3.6–10.27s (6.67s). We scroll from
  // "just before first skill" to "showing the last skills" over that window.
  // The narration timings (from beat-map) for the 3 keywords:
  //   "Content Strategy": ~0.0s into beat (at absolute 3.6s)
  //   "Copywriting":      ~1.52s into beat (at absolute 5.12s)
  //   "Campaign Planning":~2.42s into beat (at absolute 6.02s)
  // We hold at the last skill for the remaining ~4.25s of the beat.

  const coverScale = 2.0;
  const dispH      = fullH * coverScale;
  const contentH   = 1728;
  const maxScroll  = Math.max(1, dispH - contentH);

  function panYForSkill(topPx) {
    const wantDispY  = topPx * coverScale - contentH / 2;
    const panY       = Math.max(0, Math.min(100, (wantDispY / maxScroll) * 100));
    return parseFloat(panY.toFixed(1));
  }

  // Keyword timing relative to beat start (beat starts at 3.6s absolute)
  const keywordTimings = {
    'content-strategy':   0.0,
    'copywriting':        1.52,
    'campaign-planning':  2.42,
  };

  const beatDuration = 6.67; // 10.27 - 3.6s

  // Build pan_moments — start just above the first skill, hit each skill in sync
  const orderedSkills = ['content-strategy', 'copywriting', 'campaign-planning'];
  const panMoments = [];
  let lastPanY = 0;

  for (const skill of orderedSkills) {
    const pos = skillPositions[skill];
    if (!pos) continue;
    const panY = panYForSkill(pos.topPx);
    const t    = keywordTimings[skill] ?? 0;
    // Start 0.5s before the word so camera is already moving
    const atPre = Math.max(0, t - 0.3);
    if (panMoments.length === 0) {
      // Lead-in: start 0.5s above the first skill
      const leadPanY = Math.max(0, panY - 3);
      panMoments.push({ at: 0.0, x: 50, y: leadPanY });
      lastPanY = leadPanY;
    }
    panMoments.push({ at: parseFloat(atPre.toFixed(2)), x: 50, y: lastPanY });
    panMoments.push({ at: parseFloat(t.toFixed(2)),     x: 50, y: panY      });
    lastPanY = panY;
  }

  // Hold at last skill position, then slowly drift down to show more
  const driftEndPanY = Math.min(100, lastPanY + 8);
  panMoments.push({ at: 3.5,             x: 50, y: lastPanY  });
  panMoments.push({ at: beatDuration,    x: 50, y: driftEndPanY });

  // Build highlight_moments — orange box appears over each skill row
  const highlightMoments = [];
  for (const skill of orderedSkills) {
    const pos = skillPositions[skill];
    if (!pos) continue;
    const t = keywordTimings[skill] ?? 0;
    highlightMoments.push({
      at:       parseFloat(t.toFixed(2)),
      duration: 0.85,
      region: {
        x: 2,
        y: parseFloat(pos.yPct.toFixed(1)),
        w: 96,
        h: parseFloat((pos.hPct * 1.3).toFixed(1)), // 30% taller for readability
      },
    });
  }

  // ── Print timeline.json snippet ───────────────────────────────────────────
  const snippet = {
    _comment:
      'beat-keywords-bg: GitHub README scrolling — camera pans to each skill as it is spoken.',
    beat_id: 'beat-keywords-bg',
    start: 3.6,
    end: 10.27,
    asset: 'demo-frames/github-readme-scroll.png',
    display: 'guided-demo',
    guided_demo: {
      url: 'github.com/coreyhaines31/marketingskills/blob/main/README.md',
      img_width: args.viewportW,
      img_height: fullH,
      pan_moments: panMoments,
      highlight_moments: highlightMoments,
    },
  };

  console.log('\n' + '═'.repeat(60));
  console.log('PASTE THIS into timeline.json → demo lane → beat-keywords-bg:');
  console.log('═'.repeat(60));
  console.log(JSON.stringify(snippet, null, 2));
  console.log('═'.repeat(60));
  console.log(`
Next steps:
  1. Replace the beat-keywords-bg entry in timeline.json with the JSON above.
  2. Open Remotion Studio → scrub to ~3.6s and verify the scroll + highlights.
  3. Tweak pan_moments if a skill row is slightly off-center.
  4. The orange highlight box width is 96% of image width — full-row highlight
     like the reference reels. Reduce 'w' if you want a narrower box.
`);
}

main().catch((e) => {
  console.error('!! capture failed:', e.message);
  process.exit(1);
});
