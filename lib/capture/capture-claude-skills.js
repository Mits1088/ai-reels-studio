#!/usr/bin/env node
/**
 * capture-claude-skills.js
 *
 * Records 4 demo clips for the claude-skills-guide reel using the Claude Skills mock.
 *
 * Clips produced:
 *   1. demo-skill-typing.mp4      — user types skill creation prompt (beat-04)
 *   2. demo-skill-questions.mp4   — Claude asks clarifying questions (beat-05)
 *   3. demo-skill-panel.mp4       — Customize / Skills panel (beat-07)
 *   4. demo-skill-activate.mp4    — skill auto-activates in new chat (beat-08)
 *
 * Usage:
 *   node lib/capture/capture-claude-skills.js
 *   node lib/capture/capture-claude-skills.js --demo typing
 */

const { chromium } = require('playwright');
const fs   = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const ROOT    = path.resolve(__dirname, '../..');
const OUTDIR  = path.join(ROOT, 'projects/claude-skills-guide/assets');
const PUBDIR  = path.join(ROOT, 'remotion/public');
const TMPDIR  = path.join(OUTDIR, '_raw_video');
const MOCK    = path.join(__dirname, 'templates/claude-skills-mock.html');

const VIEWPORT = { width: 540, height: 960 };

fs.mkdirSync(OUTDIR, { recursive: true });
fs.mkdirSync(PUBDIR, { recursive: true });
fs.mkdirSync(TMPDIR, { recursive: true });

const args       = process.argv.slice(2);
const singleDemo = args.includes('--demo') ? args[args.indexOf('--demo') + 1] : null;

function log(m)  { console.log(m); }
function ok(m)   { console.log('✅ ' + m); }
function fail(m) { console.error('❌ ' + m); }

function convertVideo(webmPath, mp4Out, trimSec = 0) {
  const ss = trimSec > 0 ? `-ss ${trimSec}` : '';
  execSync(
    `ffmpeg -y ${ss} -i "${webmPath}" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -an "${mp4Out}"`,
    { stdio: 'pipe' }
  );
}

async function typeSlowly(page, selector, text, delayMs = 110) {
  await page.click(selector);
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(delayMs + Math.random() * 30);
  }
}

// ── Demo definitions ──────────────────────────────────────────────────────────
const DEMOS = [
  {
    id:      'typing',
    beat_id: 'beat-04',
    state:   'typing',
    outFile: 'demo-skill-typing.mp4',
    trimSec: 0.5,
    run: async (page) => {
      const mockUrl = 'file:///' + MOCK.replace(/\\/g, '/') + '#typing';
      await page.goto(mockUrl);
      await page.waitForTimeout(1200);

      // Type the full prompt slowly — this is the money shot
      const promptText = "Let's create a Claude skill. I want it to write weekly social media posts in my brand voice. Ask me whatever questions you need to make this skill excellent.";
      await typeSlowly(page, '#user-input', promptText, 80);

      // Hold so viewer reads the complete prompt
      await page.waitForTimeout(1800);
    }
  },
  {
    id:      'questions',
    beat_id: 'beat-05',
    state:   'questions',
    outFile: 'demo-skill-questions.mp4',
    trimSec: 0,
    run: async (page) => {
      const mockUrl = 'file:///' + MOCK.replace(/\\/g, '/') + '#questions';
      await page.goto(mockUrl);
      // Questions stream in automatically via JS (see mock HTML)
      // Hold for ~6s to show all 4 questions appearing
      await page.waitForTimeout(6500);
    }
  },
  {
    id:      'panel',
    beat_id: 'beat-07',
    state:   'panel',
    outFile: 'demo-skill-panel.mp4',
    trimSec: 0,
    run: async (page) => {
      const mockUrl = 'file:///' + MOCK.replace(/\\/g, '/') + '#panel';
      await page.goto(mockUrl);
      await page.waitForTimeout(500);
      // Hold panel view — viewer should see skill listed with Active badge
      await page.waitForTimeout(3500);
    }
  },
  {
    id:      'activate',
    beat_id: 'beat-08',
    state:   'activate',
    outFile: 'demo-skill-activate.mp4',
    trimSec: 0,
    run: async (page) => {
      const mockUrl = 'file:///' + MOCK.replace(/\\/g, '/') + '#activate';
      await page.goto(mockUrl);
      await page.waitForTimeout(500);
      // Banner auto-appears after 1.5s (see mock HTML)
      // Hold so viewer reads the banner clearly
      await page.waitForTimeout(4500);
    }
  }
];

(async () => {
  const demos = singleDemo ? DEMOS.filter(d => d.id === singleDemo) : DEMOS;

  if (!demos.length) {
    fail(`No demo matching "${singleDemo}". Options: typing, questions, panel, activate`);
    process.exit(1);
  }

  log('\nLaunching portrait recording browser (540×960)...');
  const browser = await chromium.launch({
    headless: false,
    args: [`--window-size=${VIEWPORT.width},${VIEWPORT.height}`, '--no-sandbox']
  });

  const ctx = await browser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: TMPDIR, size: VIEWPORT }
  });

  for (let i = 0; i < demos.length; i++) {
    const demo = demos[i];
    log(`\n${'─'.repeat(50)}`);
    log(`Demo ${i + 1}/${demos.length}: ${demo.id} (${demo.beat_id})`);
    log('─'.repeat(50));

    const page = await ctx.newPage();
    await page.setViewportSize(VIEWPORT);

    try {
      await demo.run(page);
    } catch (e) {
      fail(`Error during ${demo.id}: ${e.message}`);
    }

    // Small buffer before closing so video tail is captured
    await page.waitForTimeout(500);

    const video = page.video();
    await page.close();

    if (!video) { fail(`No video for ${demo.id}`); continue; }

    await new Promise(r => setTimeout(r, 1500));
    const webmPath = await video.path();

    if (!webmPath || !fs.existsSync(webmPath)) {
      fail(`Video file missing for ${demo.id}`);
      continue;
    }

    ok(`Raw webm: ${path.basename(webmPath)}`);

    const mp4Out    = path.join(OUTDIR, demo.outFile);
    const mp4Public = path.join(PUBDIR, demo.outFile);

    try {
      convertVideo(webmPath, mp4Out, demo.trimSec);
      ok(`MP4: ${mp4Out}`);
      fs.copyFileSync(mp4Out, mp4Public);
      ok(`Remotion public: ${demo.outFile}`);
    } catch (e) {
      fail(`FFmpeg: ${e.message}`);
    }
  }

  await ctx.close();
  await browser.close();

  log('\n' + '═'.repeat(50));
  log('All demo clips recorded.');
  log(`Assets: ${OUTDIR}`);
  log(`Public: ${PUBDIR}`);
  log('\nNext: run assemble-reel');
})();
