#!/usr/bin/env node
/**
 * capture-skilljar-scroll.js
 *
 * Records a Playwright video of https://anthropic.skilljar.com/ being
 * scrolled top-to-bottom inside a portrait viewport (540x960). Converts
 * the resulting webm into a Remotion-ready mp4 with the encoding the
 * pipeline requires (h264 yuv420p 30fps -g 1 -movflags +faststart, AAC
 * silent track).
 *
 * Used by Phase 4 (capture-demo) for the claude-managed-agents reel CTA.
 *
 * Usage:
 *   node lib/capture/capture-skilljar-scroll.js \
 *     --url https://anthropic.skilljar.com/ \
 *     --out projects/claude-managed-agents/assets/sourced/skilljar/scroll.mp4 \
 *     --duration-s 6
 */

const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

function parseArgs() {
  const a = process.argv.slice(2);
  const out = { url: 'https://anthropic.skilljar.com/', durationS: 6 };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === '--url') out.url = a[++i];
    else if (a[i] === '--out') out.out = a[++i];
    else if (a[i] === '--duration-s') out.durationS = parseFloat(a[++i]);
    else if (a[i] === '--viewport-w') out.viewportW = parseInt(a[++i], 10);
    else if (a[i] === '--viewport-h') out.viewportH = parseInt(a[++i], 10);
  }
  if (!out.out) throw new Error('--out <path.mp4> is required');
  out.viewportW ??= 540;
  out.viewportH ??= 960;
  return out;
}

async function main() {
  const args = parseArgs();
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'skilljar-cap-'));
  console.log(`  → recording ${args.url} into ${tmpDir}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: args.viewportW, height: args.viewportH },
    deviceScaleFactor: 2,
    recordVideo: {
      dir: tmpDir,
      size: { width: args.viewportW, height: args.viewportH },
    },
  });
  const page = await context.newPage();

  // Navigate. Skilljar's analytics keeps a long-poll open so 'networkidle'
  // never settles — use 'load' and then poll for the course catalog.
  await page.goto(args.url, { waitUntil: 'load', timeout: 30000 });

  // Wait until the SPA renders course catalog content. Try a few selectors
  // commonly used by Skilljar; fall back to a fixed timeout if none match.
  const catalogSelectors = [
    'div.catalog-courses',
    '[class*="course-card"]',
    '[class*="catalog"]',
    'a[href*="/path/"]',
    'a[href*="/course/"]',
  ];
  let foundSel = null;
  for (const sel of catalogSelectors) {
    try {
      await page.waitForSelector(sel, { state: 'visible', timeout: 6000 });
      foundSel = sel;
      break;
    } catch {}
  }
  if (foundSel) {
    console.log(`  → catalog ready (matched: ${foundSel})`);
  } else {
    console.log('  → no catalog selector matched — falling back to fixed wait');
    await page.waitForTimeout(5000);
  }
  // Extra settle for fonts + tile images
  await page.waitForTimeout(2000);

  // Pre-scroll pass: scroll the entire page top -> bottom -> top WITHOUT
  // recording, to trigger every lazy-loaded image / tile, then back to top.
  console.log('  → pre-scroll pass to trigger lazy loads');
  const initialHeight = await page.evaluate(
    () => document.documentElement.scrollHeight
  );
  for (let y = 0; y <= initialHeight; y += 200) {
    await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
    await page.waitForTimeout(60);
  }
  // Wait for any newly-triggered lazy images
  await page.waitForTimeout(2500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(800);

  // Recompute scrollHeight after lazy content has rendered
  const scrollHeight = await page.evaluate(
    () => document.documentElement.scrollHeight - window.innerHeight
  );
  console.log(`  → recorded scroll begins. scrollHeight=${scrollHeight}px`);

  // Hold a static frame at the top for ~0.3s so the start of the clip
  // shows the hero clearly before motion begins
  await page.waitForTimeout(300);

  // Scroll the page top -> bottom over the requested duration
  const stepCount = Math.max(60, Math.floor(args.durationS * 30));
  const stepDelayMs = (args.durationS * 1000) / stepCount;
  console.log(
    `  → scrolling ${scrollHeight}px over ${args.durationS}s (${stepCount} steps, ${stepDelayMs.toFixed(1)}ms/step)`
  );
  for (let i = 1; i <= stepCount; i++) {
    const y = Math.round((scrollHeight * i) / stepCount);
    await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
    await page.waitForTimeout(stepDelayMs);
  }
  // Hold at the bottom for ~0.5s so the closing frame settles
  await page.waitForTimeout(500);

  // Close to flush video
  await page.close();
  await context.close();
  await browser.close();

  // Find the produced webm
  const files = fs.readdirSync(tmpDir).filter((f) => f.endsWith('.webm'));
  if (!files.length) throw new Error(`No video produced in ${tmpDir}`);
  const webmPath = path.join(tmpDir, files[0]);
  const webmStats = fs.statSync(webmPath);
  console.log(`  → webm: ${webmPath} (${(webmStats.size / 1024).toFixed(0)} KB)`);

  // Re-encode to Remotion-ready mp4: h264 yuv420p 30fps -g 1 faststart + silent AAC
  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  console.log(`  → encoding mp4 → ${args.out}`);
  execFileSync(
    'ffmpeg',
    [
      '-y',
      '-i', webmPath,
      '-f', 'lavfi',
      '-i', 'anullsrc=r=44100:cl=stereo',
      '-r', '30',
      '-c:v', 'libx264',
      '-profile:v', 'high',
      '-pix_fmt', 'yuv420p',
      '-g', '1',
      '-movflags', '+faststart',
      '-c:a', 'aac',
      '-b:a', '128k',
      '-shortest',
      args.out,
    ],
    { stdio: ['ignore', 'pipe', 'pipe'] }
  );

  // Cleanup tmp
  fs.rmSync(tmpDir, { recursive: true, force: true });

  const outStats = fs.statSync(args.out);
  console.log(
    `✓ wrote ${args.out} (${(outStats.size / 1024 / 1024).toFixed(2)} MB)`
  );
}

main().catch((e) => {
  console.error('!! capture failed:', e);
  process.exit(1);
});
