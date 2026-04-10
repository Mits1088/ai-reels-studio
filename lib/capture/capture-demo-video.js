#!/usr/bin/env node
/**
 * capture-demo-video.js
 *
 * Records ChatGPT demo clips for reel production.
 *
 * Flow per demo:
 *   1. Navigate to fresh ChatGPT chat
 *   2. Type the BODY text fast (3ms/char) — viewer won't see this detail
 *   3. Position cursor at start or end depending on codePosition
 *   4. Wait 800ms so viewer sees the complete context text
 *   5. Type the CODE slowly (120ms/char) — this is the money shot
 *   6. Wait 600ms, submit
 *   7. Record 10s of response streaming
 *
 * The final MP4 is trimmed with START_TRIM_S to skip page load + fast typing.
 * Result: viewer sees body text already there, then watches the code being typed.
 *
 * Setup:
 *   1. Open Chrome with remote debugging:
 *      powershell -Command "Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' '--remote-debugging-port=9222 --user-data-dir=C:\ChromeDebug'"
 *   2. Log into ChatGPT in that Chrome window
 *   3. Run this script
 *
 * Usage:
 *   node lib/capture/capture-demo-video.js --output projects/<slug>/screenshots
 *   node lib/capture/capture-demo-video.js --demo demo-human --output ...
 */

const { chromium } = require("playwright");
const fs   = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT   = path.resolve(__dirname, "../..");
const PUBDIR = path.join(ROOT, "remotion/public");
const CONFIG = JSON.parse(fs.readFileSync(path.join(__dirname, "demo-config.json"), "utf8"));

const VIEWPORT        = { width: 540, height: 960 };
const CDP_URL         = "http://127.0.0.1:9222";
const START_TRIM_S    = 4;   // trim this many seconds from the start (page load + fast typing)
const RESPONSE_SHOW_S = 10;  // seconds to record after response starts streaming

const args       = process.argv.slice(2);
const singleDemo = args.includes("--demo")   ? args[args.indexOf("--demo")   + 1] : null;
const customOut  = args.includes("--output") ? args[args.indexOf("--output") + 1] : path.join(ROOT, "screenshots");
const OUTDIR     = path.resolve(customOut);

fs.mkdirSync(OUTDIR, { recursive: true });
fs.mkdirSync(PUBDIR, { recursive: true });

function log(msg)  { console.log(msg); }
function ok(msg)   { console.log(`✅ ${msg}`); }
function warn(msg) { console.warn(`⚠  ${msg}`); }
function fail(msg) { console.error(`❌ ${msg}`); }

// ── Inject CSS: zoom chat area, hide sidebar ──────────────────────────────────
async function focusChatArea(page) {
  await page.addStyleTag({ content: `
    nav, [data-testid="sidebar"], aside { display: none !important; }
    html { zoom: 1.3 !important; }
    main { max-width: 100% !important; padding: 0 !important; }
  ` }).catch(() => {});
}

// ── Find the chat input ────────────────────────────────────────────────────────
async function findInput(page) {
  const selectors = [
    '[data-testid="prompt-textarea"]',
    '#prompt-textarea',
    '[contenteditable="true"][data-id]',
    'div[contenteditable="true"]',
    'textarea[placeholder]',
    'textarea',
  ];
  for (const sel of selectors) {
    try {
      const el = page.locator(sel).first();
      await el.waitFor({ timeout: 5000, state: "visible" });
      return el;
    } catch (_) {}
  }
  throw new Error("No chat input found");
}

// ── Type text character by character ─────────────────────────────────────────
async function typeSlowly(page, text, delayMs = 120) {
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(delayMs + Math.random() * 20);
  }
}

// ── Type text fast (pre-fill body — not the demo focus) ──────────────────────
async function typeFast(page, text) {
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(3 + Math.random() * 2);
  }
}

// ── Scroll follower during response ─────────────────────────────────────────
function startScrollFollower(page) {
  let active = true;
  (async () => {
    while (active) {
      await page.evaluate(() =>
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })
      ).catch(() => {});
      await new Promise((r) => setTimeout(r, 400));
    }
  })();
  return () => { active = false; };
}

// ── Convert webm → mp4, trimming first N seconds ─────────────────────────────
function convertVideo(webmPath, mp4Out, trimSeconds = 0) {
  const ssArg = trimSeconds > 0 ? `-ss ${trimSeconds}` : "";
  execSync(
    `ffmpeg -y ${ssArg} -i "${webmPath}" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -an "${mp4Out}"`,
    { stdio: "pipe" }
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────
(async () => {
  const tmpVideoDir = path.join(OUTDIR, "_raw_video");
  fs.mkdirSync(tmpVideoDir, { recursive: true });

  // Connect to user's running Chrome to grab session cookies
  log(`\nConnecting to Chrome at ${CDP_URL}...`);
  log(`Make sure Chrome is open at chatgpt.com and you're logged in.\n`);

  let cdpBrowser;
  try {
    cdpBrowser = await chromium.connectOverCDP(CDP_URL);
    ok("Connected to Chrome.");
  } catch (e) {
    fail(`Cannot connect to Chrome: ${e.message}`);
    fail(`Start Chrome with remote debugging:`);
    fail(`  powershell -Command "Start-Process 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' '--remote-debugging-port=9222 --user-data-dir=C:\\ChromeDebug'"`);
    process.exit(1);
  }

  const existingCtx = cdpBrowser.contexts()[0];
  const cookies = await existingCtx.cookies(["https://chatgpt.com", "https://chat.openai.com"]);
  log(`  Grabbed ${cookies.length} cookies from your session.`);
  await cdpBrowser.close();

  if (cookies.length === 0) {
    warn("No ChatGPT cookies found — open ChatGPT in Chrome and try again.");
  }

  // Launch a clean recording browser
  log(`\nLaunching recording browser (portrait 9:16)...`);
  const recordBrowser = await chromium.launch({
    headless: false,
    ignoreDefaultArgs: ["--enable-automation"],
    args: [
      "--no-sandbox",
      "--disable-blink-features=AutomationControlled",
      `--window-size=${VIEWPORT.width},${VIEWPORT.height}`,
    ],
  });

  const recordCtx = await recordBrowser.newContext({
    viewport: VIEWPORT,
    recordVideo: { dir: tmpVideoDir, size: VIEWPORT },
  });

  if (cookies.length > 0) {
    await recordCtx.addCookies(cookies);
  }

  const demos = singleDemo
    ? CONFIG.demos.filter((d) => d.id === singleDemo)
    : CONFIG.demos;

  if (!demos.length) {
    fail(`No demos found${singleDemo ? ` matching "${singleDemo}"` : ""}`);
    await recordBrowser.close();
    process.exit(1);
  }

  for (let i = 0; i < demos.length; i++) {
    const demo = demos[i];

    log(`\n${"═".repeat(60)}`);
    log(`Demo ${i + 1}/${demos.length}: ${demo.id}`);
    log(`  Body (fast):  "${demo.body.slice(0, 60)}..."`);
    log(`  Code (slow):  "${demo.code}" → ${demo.codePosition}`);
    log("═".repeat(60));

    const page = i === 0
      ? await recordCtx.newPage()
      : recordCtx.pages()[recordCtx.pages().length - 1];

    await page.setViewportSize(VIEWPORT);

    // Navigate to fresh ChatGPT chat
    await page.goto("https://chatgpt.com/", { timeout: 30000, waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);

    // Dismiss banners
    for (const btn of ["Accept all", "Reject non-essential", "Got it", "OK"]) {
      await page.getByRole("button", { name: btn, exact: true }).click({ timeout: 800 }).catch(() => {});
    }

    await focusChatArea(page);
    await page.waitForTimeout(500);

    // Find input and click it
    const input = await findInput(page);
    await input.click();

    // ── STEP 1: Type body text FAST (nearly instant) ──────────────────────────
    log("  Fast-typing body text...");
    await typeFast(page, demo.body);
    await page.waitForTimeout(400);

    // ── STEP 2: Position cursor ───────────────────────────────────────────────
    if (demo.codePosition === "start") {
      // /human: go to very beginning so code is prepended
      log("  Moving cursor to start...");
      await page.keyboard.press("Control+Home");
      await page.waitForTimeout(300);
    } else {
      // others: cursor stays at end (it's already there after fast typing)
      log("  Cursor at end, ready to append code...");
      await page.keyboard.press("End");
      await page.waitForTimeout(300);
    }

    // ── STEP 3: Pause so viewer sees the complete context text ────────────────
    // (The START_TRIM_S will cut the page-load + fast-typing, leaving this pause
    //  as the first visible frame — body text already in the box)
    await page.waitForTimeout(800);

    // ── STEP 4: Type the CODE slowly — this is the money shot ─────────────────
    log(`  Typing code "${demo.code}" slowly...`);
    await typeSlowly(page, demo.code, 120);

    // Pause so viewer reads the complete prompt before submit
    await page.waitForTimeout(700);

    // ── STEP 5: Submit ────────────────────────────────────────────────────────
    log("  Submitting...");
    await page.keyboard.press("Enter");

    // Wait for response to start (stop-button appears)
    log("  Waiting for response to start...");
    await page.waitForSelector('[data-testid="stop-button"]', { timeout: 15000 }).catch(() => {});

    // Scroll-follow and capture response
    const stopScroll = startScrollFollower(page);
    log(`  Recording ${RESPONSE_SHOW_S}s of response...`);
    await page.waitForTimeout(RESPONSE_SHOW_S * 1000);
    stopScroll();

    // Open next page before closing current (keeps recordCtx alive)
    if (i < demos.length - 1) {
      await recordCtx.newPage().then((p) => p.setViewportSize(VIEWPORT));
    }

    const video = page.video();
    await page.close();

    if (!video) {
      fail(`No video for ${demo.id}`);
      continue;
    }

    await new Promise((r) => setTimeout(r, 1500));
    const webmPath = await video.path();

    if (!webmPath || !fs.existsSync(webmPath)) {
      fail(`Video file missing for ${demo.id}`);
      continue;
    }

    ok(`Raw webm: ${path.basename(webmPath)}`);

    const mp4Name   = `${demo.id}-response.mp4`;
    const mp4Out    = path.join(OUTDIR, mp4Name);
    const mp4Public = path.join(PUBDIR, demo.target_asset);

    try {
      convertVideo(webmPath, mp4Out, START_TRIM_S);
      ok(`MP4 (trimmed ${START_TRIM_S}s): ${mp4Out}`);
      fs.copyFileSync(mp4Out, mp4Public);
      ok(`Remotion public: ${demo.target_asset}`);
    } catch (e) {
      fail(`FFmpeg: ${e.message}`);
    }
  }

  await recordCtx.close();
  await recordBrowser.close();

  log(`\n${"═".repeat(60)}`);
  log("✅ All demos recorded");
  log(`   Videos : ${OUTDIR}`);
  log(`   Public  : ${PUBDIR}`);
  log(`\nNext: run clip-demos.js to trim + speed-adjust the response sections.`);
  log(`      Check frame timestamps in screenshots/frames/ to set typingEnd values.`);
})();
