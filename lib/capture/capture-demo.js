#!/usr/bin/env node
/**
 * capture-demo.js
 *
 * Capture demo screenshots for reel production with a 3-stage fallback:
 *
 *   Stage 1 — Real ChatGPT via Playwright
 *             Navigate to chat.openai.com, type the prompt, wait for response,
 *             screenshot at key moments, extract DOM bounding boxes for zoom coords.
 *             Skip to Stage 2 if blocked (login wall, CAPTCHA, rate limit).
 *
 *   Stage 2 — Manual screenshots from user
 *             Check screenshots/manual/ for pre-supplied screenshots.
 *             If found, read them for zoom calibration.
 *             If not found, prompt user to supply them and wait.
 *             Skip to Stage 3 if user declines.
 *
 *   Stage 3 — Mock ChatGPT HTML (always works)
 *             Load lib/capture/templates/chatgpt-mock.html in headless browser.
 *             Inject prompt and response text from demo-config.json.
 *             Screenshot at two states (prompt only, then with response).
 *             Auto-calculate zoom coordinates from DOM bounding boxes.
 *             Output is production-ready PNG + zoom-hints.json.
 *
 * Usage:
 *   node lib/capture/capture-demo.js
 *   node lib/capture/capture-demo.js --stage 3          (skip straight to mock)
 *   node lib/capture/capture-demo.js --demo el10        (single demo only)
 *   node lib/capture/capture-demo.js --no-interactive   (CI mode, auto-fall to mock)
 *
 * Output:
 *   screenshots/<demo-id>-prompt.png
 *   screenshots/<demo-id>-response.png
 *   screenshots/zoom-hints.json   ← pre-calculated zoom_moments for timeline.json
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const readline = require("readline");

const ROOT    = path.resolve(__dirname, "../..");
const SCRNDIR = path.join(ROOT, "screenshots");
const MANUAL  = path.join(SCRNDIR, "manual");
const PUBDIR  = path.join(ROOT, "remotion/public");
const MOCK    = path.join(__dirname, "templates/chatgpt-mock.html");

const CONFIG  = JSON.parse(
  fs.readFileSync(path.join(__dirname, "demo-config.json"), "utf8")
);

// ── Viewport matches typical screenshot dimensions (landscape, 16:9) ──────────
const VIEWPORT = { width: 1280, height: 720 };

// ── Coordinate formula (contain+top letterbox) ────────────────────────────────
// The screenshot is 1280×720. When displayed in the reel's split-screen container
// (roughly square, 1024×1016) with objectFit:contain + objectPosition:top:
//   image fills full width → x maps 1:1
//   image occupies top 57% of container height → frame_y = image_y * 0.57
function toFrameCoords(box, viewport) {
  const image_x = ((box.x + box.width  / 2) / viewport.width)  * 100;
  const image_y = ((box.y + box.height / 2) / viewport.height) * 100;
  return {
    x: Math.round(image_x),
    y: Math.round(image_y * 0.57),
    image_x: Math.round(image_x),
    image_y: Math.round(image_y),
  };
}

// ── CLI args ──────────────────────────────────────────────────────────────────
const args        = process.argv.slice(2);
const forceStage  = args.includes("--stage")  ? parseInt(args[args.indexOf("--stage")  + 1]) : null;
const singleDemo  = args.includes("--demo")   ? args[args.indexOf("--demo")   + 1] : null;
const noInteract  = args.includes("--no-interactive");
const useClause   = args.includes("--claude");   // connect to existing Chrome session via CDP
const cdpPort     = args.includes("--cdp-port") ? parseInt(args[args.indexOf("--cdp-port") + 1]) : 9222;
const customOut   = args.includes("--output")  ? args[args.indexOf("--output")  + 1] : null;

// ── Helpers ───────────────────────────────────────────────────────────────────
function ask(question) {
  if (noInteract) return Promise.resolve("n");
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (ans) => { rl.close(); resolve(ans.trim().toLowerCase()); }));
}

function log(msg)  { console.log(msg); }
function warn(msg) { console.warn(`⚠  ${msg}`); }
function ok(msg)   { console.log(`✅ ${msg}`); }
function fail(msg) { console.error(`❌ ${msg}`); }

// Allow --output to override the screenshots directory (e.g. per-project folder)
const OUTDIR = customOut ? path.resolve(customOut) : SCRNDIR;
fs.mkdirSync(OUTDIR,  { recursive: true });
fs.mkdirSync(MANUAL,  { recursive: true });

// ═══════════════════════════════════════════════════════════════════════════════
// STAGE 1: Real ChatGPT
// ═══════════════════════════════════════════════════════════════════════════════
async function tryChatGPT(page, demo) {
  log("\n[Stage 1] Attempting real ChatGPT...");

  try {
    await page.goto("https://chat.openai.com", { timeout: 15000, waitUntil: "domcontentloaded" });
  } catch (e) {
    warn("Navigation failed (timeout or network)");
    return null;
  }

  // Detect blocking conditions
  const blocked = await isBlocked(page);
  if (blocked) {
    warn(`Blocked: ${blocked}`);
    return null;
  }

  try {
    // Find the prompt input
    const input = page.locator('[data-testid="prompt-textarea"], #prompt-textarea, [placeholder*="Message"]').first();
    await input.waitFor({ timeout: 8000 });
    await input.fill(demo.prompt);
    await input.press("Enter");

    // Wait for response to finish streaming (stop button disappears)
    await page.waitForSelector('[data-testid="stop-button"]', { timeout: 5000 }).catch(() => {});
    await page.waitForSelector('[data-testid="stop-button"]', { state: "detached", timeout: 30000 });

    // Screenshot: prompt visible, response visible
    const screenshotPath = path.join(OUTDIR, `${demo.id}-response.png`);
    await page.screenshot({ path: screenshotPath, clip: { x: 0, y: 0, ...VIEWPORT } });

    // Try to get bounding boxes for zoom coord calculation
    const promptBox   = await page.locator('[data-message-author-role="user"]').last().boundingBox().catch(() => null);
    const responseBox = await page.locator('[data-message-author-role="assistant"]').last().boundingBox().catch(() => null);

    ok(`Captured from real ChatGPT: ${screenshotPath}`);
    return {
      source: "chatgpt-real",
      screenshots: { response: screenshotPath },
      coords: {
        zoom1: promptBox   ? toFrameCoords(promptBox, VIEWPORT)   : null,
        zoom2: responseBox ? toFrameCoords(responseBox, VIEWPORT) : null,
      },
    };
  } catch (e) {
    warn(`Capture failed: ${e.message}`);
    return null;
  }
}

async function isBlocked(page) {
  const url = page.url();
  if (url.includes("/auth/") || url.includes("/login") || url.includes("auth0"))
    return "login/auth wall";

  const bodyText = await page.locator("body").textContent({ timeout: 3000 }).catch(() => "");
  if (/captcha|verify you are human|unusual traffic/i.test(bodyText)) return "CAPTCHA";
  if (/access denied|403 forbidden/i.test(bodyText))                   return "access denied";
  if (/sign in|log in to continue/i.test(bodyText))                    return "login required";

  return null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// STAGE 2: Manual screenshots
// ═══════════════════════════════════════════════════════════════════════════════
async function tryManualScreenshots(demo) {
  log("\n[Stage 2] Checking for manual screenshots...");

  const expectedFiles = [
    `${demo.id}-prompt.png`,
    `${demo.id}-response.png`,
  ];

  const found = expectedFiles.filter((f) => fs.existsSync(path.join(MANUAL, f)));

  if (found.length > 0) {
    ok(`Found ${found.length}/${expectedFiles.length} manual screenshots in screenshots/manual/`);
    // Copy to main screenshots folder
    const copied = {};
    for (const f of found) {
      const src = path.join(MANUAL, f);
      const dst = path.join(SCRNDIR, f);
      fs.copyFileSync(src, dst);
      copied[f.replace(`${demo.id}-`, "").replace(".png", "")] = dst;
    }
    log("  ⚠  Zoom coordinates cannot be auto-calculated from manual screenshots.");
    log("     Share them with Claude after this run to get correct zoom_moments.");
    return { source: "manual", screenshots: copied, coords: null };
  }

  // Not found — prompt user
  log(`  No manual screenshots found in: screenshots/manual/`);
  log(`  Expected filenames:`);
  for (const f of expectedFiles) log(`    • ${f}`);
  log(`  Drop your screenshots there now, then answer below.`);

  const ans = await ask("  Do you have screenshots ready? (y/n/skip): ");

  if (ans === "y" || ans === "yes") {
    const stillFound = expectedFiles.filter((f) => fs.existsSync(path.join(MANUAL, f)));
    if (stillFound.length > 0) {
      ok(`Found ${stillFound.length} screenshot(s). Continuing.`);
      const copied = {};
      for (const f of stillFound) {
        const dst = path.join(SCRNDIR, f);
        fs.copyFileSync(path.join(MANUAL, f), dst);
        copied[f.replace(`${demo.id}-`, "").replace(".png", "")] = dst;
      }
      return { source: "manual", screenshots: copied, coords: null };
    }
    warn("Still not found. Falling through to Stage 3.");
  }

  return null;
}

// ═══════════════════════════════════════════════════════════════════════════════
// STAGE 3: Mock ChatGPT HTML
// ═══════════════════════════════════════════════════════════════════════════════
async function generateFromMock(page, demo) {
  log("\n[Stage 3] Generating from mock ChatGPT HTML...");

  if (!fs.existsSync(MOCK)) {
    fail(`Mock template not found: ${MOCK}`);
    return null;
  }

  const mockUrl = `file:///${MOCK.replace(/\\/g, "/")}`;
  await page.goto(mockUrl, { waitUntil: "networkidle" });

  // ── Screenshot 1: prompt only ─────────────────────────────────────────────
  await page.evaluate((d) => window.applyContent({
    prompt:   d.prompt_html ?? d.prompt,
    show:     "prompt",
    title:    d.id,
    model:    "GPT-4o",
  }), demo);

  await page.waitForTimeout(300); // let fonts/layout settle

  const promptPath = path.join(OUTDIR, `${demo.id}-prompt.png`);
  await page.screenshot({ path: promptPath });
  ok(`Prompt screenshot: ${path.basename(promptPath)}`);

  // Get bounding box of the user message for zoom coord 1
  const promptBox = await page.locator("#user-message").boundingBox();

  // ── Screenshot 2: prompt + response ──────────────────────────────────────
  await page.evaluate((d) => window.applyContent({
    prompt:   d.prompt_html ?? d.prompt,
    response: d.response_html,
    show:     "both",
    title:    d.id,
    model:    "GPT-4o",
  }), demo);

  await page.waitForTimeout(300);

  const responsePath = path.join(OUTDIR, `${demo.id}-response.png`);
  await page.screenshot({ path: responsePath });
  ok(`Response screenshot: ${path.basename(responsePath)}`);

  // Also save response copy to remotion/public as a usable demo asset
  const publicPath = path.join(PUBDIR, demo.target_asset ?? `demo-${demo.id}.png`);
  fs.copyFileSync(responsePath, publicPath);
  ok(`Copied to remotion/public: ${path.basename(publicPath)}`);

  // Get bounding box of assistant message for zoom coord 2
  const responseBox = await page.locator("#assistant-message").boundingBox();

  const coords = {
    zoom1: promptBox   ? toFrameCoords(promptBox,   VIEWPORT) : null,
    zoom2: responseBox ? toFrameCoords(responseBox, VIEWPORT) : null,
  };

  log(`  Zoom coords (frame space, contain+top formula):`);
  log(`    Zoom 1 (prompt)  : x:${coords.zoom1?.x}, y:${coords.zoom1?.y}`);
  log(`    Zoom 2 (response): x:${coords.zoom2?.x}, y:${coords.zoom2?.y}`);

  return {
    source: "mock",
    screenshots: { prompt: promptPath, response: responsePath, public: publicPath },
    coords,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════
(async () => {
  let browser, page;

  if (useClause) {
    // --claude: connect to the user's existing Chrome session via CDP
    // Chrome must be running with --remote-debugging-port=<cdpPort> (default 9222)
    // The Claude browser extension typically enables this automatically.
    try {
      log(`[--claude] Connecting to Chrome via CDP at http://localhost:${cdpPort}...`);
      browser = await chromium.connectOverCDP(`http://localhost:${cdpPort}`);
      const ctx = browser.contexts()[0];
      page = await ctx.newPage();
      await page.setViewportSize(VIEWPORT);
      ok("Connected to your Chrome session — ChatGPT login state will be used.");
    } catch (e) {
      warn(`CDP connection failed (${e.message}). Falling back to Chrome with your saved profile...`);
      // Fallback: launch Chrome with the user's real profile (preserves all cookies/logins)
      const userDataDir = process.env.CHROME_USER_DATA ||
        path.join(process.env.USERPROFILE || process.env.HOME || "C:/Users/no_1_",
          "AppData/Local/Google/Chrome/User Data");
      log(`  Using Chrome profile at: ${userDataDir}`);
      const ctx = await chromium.launchPersistentContext(userDataDir, {
        channel:  "chrome",
        headless: false,
        viewport: VIEWPORT,
        args:     ["--no-sandbox"],
      });
      page    = await ctx.newPage();
      browser = { close: () => ctx.close() };
      ok("Launched Chrome with your saved profile.");
    }
  } else {
    browser = await chromium.launch({ headless: true });
    page    = await browser.newPage();
    await page.setViewportSize(VIEWPORT);
  }

  const demos = singleDemo
    ? CONFIG.demos.filter((d) => d.id === singleDemo)
    : CONFIG.demos;

  if (demos.length === 0) {
    fail(`No demos found${singleDemo ? ` with id "${singleDemo}"` : ""}`);
    await browser.close();
    process.exit(1);
  }

  const zoomHints = [];

  for (const demo of demos) {
    log(`\n${"═".repeat(60)}`);
    log(`Demo: ${demo.id} (${demo.beat_id})`);
    log("═".repeat(60));

    let result = null;

    if (!forceStage || forceStage === 1) {
      result = await tryChatGPT(page, demo);
    }

    if (!result && (!forceStage || forceStage <= 2)) {
      result = await tryManualScreenshots(demo);
    }

    if (!result) {
      result = await generateFromMock(page, demo);
    }

    if (!result) {
      fail(`All stages failed for demo: ${demo.id}`);
      continue;
    }

    // Build zoom_moments for timeline.json
    const zoomMoments = [];
    if (result.coords?.zoom1) {
      zoomMoments.push({
        at: demo.zoom_at?.[0] ?? 0.6,
        x: result.coords.zoom1.x,
        y: result.coords.zoom1.y,
        scale: 2.4,
        holdFor: 2.0,
      });
    }
    if (result.coords?.zoom2) {
      zoomMoments.push({
        at: demo.zoom_at?.[1] ?? 3.0,
        x: result.coords.zoom2.x,
        y: result.coords.zoom2.y,
        scale: 2.0,
        holdFor: 2.0,
      });
    }

    zoomHints.push({
      id:          demo.id,
      beat_id:     demo.beat_id,
      source:      result.source,
      asset:       demo.target_asset,
      screenshots: result.screenshots,
      zoom_moments: zoomMoments,
      _note: result.source === "manual"
        ? "Zoom coords not auto-calculated — share screenshots with Claude for calibration"
        : "Zoom coords auto-calculated from DOM bounding boxes",
    });
  }

  await browser.close();

  // ── Write zoom hints ───────────────────────────────────────────────────────
  const hintsPath = path.join(OUTDIR, "zoom-hints.json");
  fs.writeFileSync(hintsPath, JSON.stringify(zoomHints, null, 2));

  log(`\n${"═".repeat(60)}`);
  log("✅ Done");
  log(`   Screenshots : ${SCRNDIR}`);
  log(`   Zoom hints  : ${hintsPath}`);
  log(`\nNext steps:`);
  log(`  • Review screenshots/ to verify content is correct`);
  log(`  • Run: node lib/capture/apply-zoom-hints.js`);
  log(`    (updates timeline.json broll lane with calculated zoom_moments)`);
  log(`  • Or share screenshots with Claude for manual calibration`);
})();
