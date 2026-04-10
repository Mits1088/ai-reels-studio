#!/usr/bin/env node
/**
 * source-brief.js
 *
 * Phase 0 of reel production. Given a URL containing AI tool features,
 * demos, or screenshots:
 *
 *   1. Fetch page content (text extraction for Claude to analyse)
 *   2. Full-page screenshot
 *   3. Screenshot each major section (detected by headings / landmark elements)
 *   4. Download any images or video posters linked on the page
 *   5. Write source-research.md — structured intelligence for brief + script
 *   6. Pre-populate demo-config.json with prompts/responses found on the page
 *
 * Usage:
 *   node lib/capture/source-brief.js --url https://... --project my-reel-slug
 *   node lib/capture/source-brief.js --url https://... --project my-reel-slug --full-page
 *   node lib/capture/source-brief.js --url https://... --project my-reel-slug --sections-only
 *
 * Outputs (all relative to project folder):
 *   projects/<slug>/assets/source/          ← downloaded images + screenshots
 *   projects/<slug>/source-research.md      ← structured intelligence
 *   projects/<slug>/source-research.json    ← machine-readable version
 *   lib/capture/demo-config.json            ← pre-populated for capture-demo.js
 */

const { chromium } = require("playwright");
const fs   = require("fs");
const path = require("path");
const https = require("https");
const http  = require("http");
const { URL } = require("url");

const ROOT = path.resolve(__dirname, "../..");

// ── Args ──────────────────────────────────────────────────────────────────────
const args        = process.argv.slice(2);
const urlFlag     = args.includes("--url")     ? args[args.indexOf("--url")     + 1] : null;
const projectFlag = args.includes("--project") ? args[args.indexOf("--project") + 1] : null;
const fullPage    = args.includes("--full-page");
const sectionsOnly = args.includes("--sections-only");

if (!urlFlag) {
  console.error("❌ --url is required");
  console.error("   Usage: node lib/capture/source-brief.js --url https://... --project <slug>");
  process.exit(1);
}

if (!projectFlag) {
  console.error("❌ --project is required (the reel slug, e.g. my-reel-name)");
  process.exit(1);
}

const PROJECT_DIR = path.join(ROOT, "projects", projectFlag);
const ASSETS_DIR  = path.join(PROJECT_DIR, "assets", "source");
const SCRNDIR     = path.join(PROJECT_DIR, "assets", "source", "screenshots");

fs.mkdirSync(ASSETS_DIR, { recursive: true });
fs.mkdirSync(SCRNDIR,    { recursive: true });

// ── Helpers ───────────────────────────────────────────────────────────────────
function log(msg)  { console.log(msg); }
function ok(msg)   { console.log(`✅ ${msg}`); }
function warn(msg) { console.warn(`⚠  ${msg}`); }
function fail(msg) { console.error(`❌ ${msg}`); }

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const proto = url.startsWith("https") ? https : http;
    const file  = fs.createWriteStream(dest);
    proto.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        return downloadFile(res.headers.location, dest).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on("finish", () => { file.close(); resolve(dest); });
    }).on("error", (e) => { fs.unlink(dest, () => {}); reject(e); });
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
(async () => {
  log(`\nSource Brief — Phase 0`);
  log(`URL     : ${urlFlag}`);
  log(`Project : ${projectFlag}`);
  log(`Output  : ${PROJECT_DIR}\n`);

  const browser = await chromium.launch({ headless: true });
  const page    = await browser.newPage();

  await page.setViewportSize({ width: 1440, height: 900 });

  // ── Navigate ────────────────────────────────────────────────────────────────
  log("Navigating to URL...");
  try {
    await page.goto(urlFlag, { waitUntil: "networkidle", timeout: 30000 });
  } catch (e) {
    warn(`Page load timed out or errored: ${e.message}`);
    warn("Continuing with partial content...");
  }

  // Dismiss cookie banners / popups
  for (const selector of [
    '[aria-label*="cookie" i] button',
    'button[id*="accept" i]',
    'button[class*="accept" i]',
    '[data-testid*="cookie-accept"]',
    '.cookie-banner button',
  ]) {
    await page.locator(selector).first().click({ timeout: 1500 }).catch(() => {});
  }

  await page.waitForTimeout(1000);

  // ── Full-page screenshot ────────────────────────────────────────────────────
  if (!sectionsOnly) {
    const fullPath = path.join(SCRNDIR, "00-full-page.png");
    await page.screenshot({ path: fullPath, fullPage: true });
    ok(`Full-page screenshot: ${path.basename(fullPath)}`);
  }

  // ── Extract page text ───────────────────────────────────────────────────────
  log("Extracting page content...");

  const pageData = await page.evaluate(() => {
    const title       = document.title;
    const metaDesc    = document.querySelector('meta[name="description"]')?.content ?? "";
    const ogTitle     = document.querySelector('meta[property="og:title"]')?.content ?? "";
    const ogDesc      = document.querySelector('meta[property="og:description"]')?.content ?? "";

    // Extract sections by heading
    const sections = [];
    const headings = document.querySelectorAll("h1, h2, h3");
    headings.forEach((h) => {
      const text = h.textContent.trim();
      if (!text || text.length < 3) return;

      // Gather paragraph/list text following this heading
      let body = "";
      let el   = h.nextElementSibling;
      let count = 0;
      while (el && !["H1","H2","H3"].includes(el.tagName) && count < 5) {
        const t = el.textContent.trim();
        if (t.length > 10) body += t + " ";
        el = el.nextElementSibling;
        count++;
      }

      sections.push({ heading: text, body: body.trim().slice(0, 600) });
    });

    // Extract all images
    const images = Array.from(document.querySelectorAll("img"))
      .map((img) => ({
        src: img.src,
        alt: img.alt,
        width: img.naturalWidth || img.width,
        height: img.naturalHeight || img.height,
      }))
      .filter((img) => img.src && img.width > 200 && img.height > 100);

    // Extract video sources / posters
    const videos = Array.from(document.querySelectorAll("video, [data-src$='.mp4'], source"))
      .map((v) => ({
        src:    v.src || v.dataset?.src || v.querySelector?.("source")?.src || "",
        poster: v.poster ?? "",
        type:   v.tagName,
      }))
      .filter((v) => v.src || v.poster);

    // Extract any code blocks (may contain prompt examples)
    const codeBlocks = Array.from(document.querySelectorAll("code, pre"))
      .map((c) => c.textContent.trim())
      .filter((c) => c.length > 10 && c.length < 500);

    // Extract any explicit feature lists
    const featureLists = Array.from(document.querySelectorAll("ul li, ol li"))
      .map((li) => li.textContent.trim())
      .filter((li) => li.length > 15 && li.length < 300)
      .slice(0, 30);

    return { title, metaDesc, ogTitle, ogDesc, sections, images, videos, codeBlocks, featureLists };
  });

  ok(`Page extracted: ${pageData.sections.length} sections, ${pageData.images.length} images, ${pageData.videos.length} videos`);

  // ── Screenshot each section ─────────────────────────────────────────────────
  log("Screenshotting key sections...");
  const sectionScreenshots = [];

  const sectionEls = await page.locator("section, [class*='feature'], [class*='demo'], [class*='hero'], h2").all();
  let sIdx = 0;

  for (const el of sectionEls.slice(0, 12)) {
    try {
      const box = await el.boundingBox();
      if (!box || box.height < 100) continue;

      const label    = slugify(await el.textContent().catch(() => `section-${sIdx}`)) || `section-${sIdx}`;
      const filename = `${String(sIdx + 1).padStart(2, "0")}-${label}.png`;
      const outPath  = path.join(SCRNDIR, filename);

      // Expand bounding box to capture context
      await page.screenshot({
        path: outPath,
        clip: {
          x:      Math.max(0, box.x - 20),
          y:      Math.max(0, box.y - 20),
          width:  Math.min(1440, box.width + 40),
          height: Math.min(1200, box.height + 60),
        },
      });

      sectionScreenshots.push({ index: sIdx + 1, filename, label, box });
      sIdx++;
    } catch (_) {}
  }

  ok(`Section screenshots: ${sectionScreenshots.length}`);

  // ── Download images ─────────────────────────────────────────────────────────
  log("Downloading page images...");
  const downloadedImages = [];

  for (const img of pageData.images.slice(0, 20)) {
    try {
      const imgUrl  = new URL(img.src, urlFlag).href;
      const ext     = path.extname(new URL(imgUrl).pathname).split("?")[0] || ".png";
      const fname   = `img-${slugify(img.alt || path.basename(imgUrl, ext)).slice(0, 40)}${ext}`;
      const outPath = path.join(ASSETS_DIR, fname);

      await downloadFile(imgUrl, outPath);
      downloadedImages.push({ filename: fname, alt: img.alt, width: img.width, height: img.height });
    } catch (_) {}
  }

  ok(`Images downloaded: ${downloadedImages.length}`);

  // ── Download video posters ──────────────────────────────────────────────────
  const downloadedPosters = [];
  for (const vid of pageData.videos) {
    if (!vid.poster) continue;
    try {
      const posterUrl = new URL(vid.poster, urlFlag).href;
      const fname     = `poster-${slugify(path.basename(posterUrl))}.jpg`;
      const outPath   = path.join(ASSETS_DIR, fname);
      await downloadFile(posterUrl, outPath);
      downloadedPosters.push(fname);
    } catch (_) {}
  }

  await browser.close();

  // ── Build source-research.md ────────────────────────────────────────────────
  log("Writing source-research.md...");

  const researchPath = path.join(PROJECT_DIR, "source-research.md");

  const featuresBlock = pageData.sections
    .map((s, i) => `### ${i + 1}. ${s.heading}\n${s.body}`)
    .join("\n\n");

  const featureListBlock = pageData.featureLists.length
    ? pageData.featureLists.map((f) => `- ${f}`).join("\n")
    : "_none detected_";

  const codeBlock = pageData.codeBlocks.length
    ? pageData.codeBlocks.map((c) => `\`\`\`\n${c}\n\`\`\``).join("\n\n")
    : "_none detected_";

  const imgBlock = downloadedImages
    .map((img) => `- \`${img.filename}\` — "${img.alt}" (${img.width}×${img.height})`)
    .join("\n") || "_none_";

  const screenshotBlock = sectionScreenshots
    .map((s) => `- \`screenshots/${s.filename}\` — ${s.label}`)
    .join("\n") || "_none_";

  const md = `# Source Research — ${projectFlag}

**URL**: ${urlFlag}
**Captured**: ${new Date().toISOString().slice(0, 10)}

---

## Page Overview

- **Title**: ${pageData.title}
- **Description**: ${pageData.metaDesc || pageData.ogDesc || "_not found_"}
- **OG Title**: ${pageData.ogTitle || "_not found_"}

---

## Feature Sections

${featuresBlock || "_No sections detected_"}

---

## Feature List (bullet points found on page)

${featureListBlock}

---

## Code / Prompt Examples Found

${codeBlock}

---

## Assets Available

### Downloaded images (${downloadedImages.length})
${imgBlock}

### Section screenshots (${sectionScreenshots.length})
${screenshotBlock}

### Video content
${pageData.videos.length > 0
  ? pageData.videos.map((v) => `- ${v.type}: ${v.src || v.poster}`).join("\n")
  : "_none detected_"}

---

## Claude — Action Required

Review the sections above and produce:

1. **Hook** — the single most surprising or valuable claim on this page (1 sentence)
2. **3 support points** — the strongest features or demo steps (pick from sections above)
3. **CTA** — what should the viewer do after watching?
4. **Demo candidates** — which features should be shown on screen?
5. **Script direction** — what tone does this content suit? (educational / hype / comparison)
6. **Assets to use directly** — which downloaded screenshots can go straight into the reel?
7. **Assets still needed** — what needs to be captured via capture-demo.js?

Do not proceed to new-reel until the user has confirmed the brief direction.
`;

  fs.writeFileSync(researchPath, md);
  ok(`source-research.md written`);

  // ── Write machine-readable JSON ─────────────────────────────────────────────
  const jsonPath = path.join(PROJECT_DIR, "source-research.json");
  fs.writeFileSync(jsonPath, JSON.stringify({
    url:        urlFlag,
    project:    projectFlag,
    captured:   new Date().toISOString(),
    page:       { title: pageData.title, description: pageData.metaDesc || pageData.ogDesc },
    sections:   pageData.sections,
    features:   pageData.featureLists,
    codeBlocks: pageData.codeBlocks,
    assets: {
      images:      downloadedImages,
      posters:     downloadedPosters,
      screenshots: sectionScreenshots.map((s) => s.filename),
    },
  }, null, 2));

  // ── Pre-populate demo-config.json ───────────────────────────────────────────
  // Pull any prompt-like code blocks as starting points for demos
  const demoConfigPath = path.join(__dirname, "demo-config.json");
  let existingConfig   = {};
  try { existingConfig = JSON.parse(fs.readFileSync(demoConfigPath, "utf8")); } catch (_) {}

  if (pageData.codeBlocks.length > 0) {
    const suggestedDemos = pageData.codeBlocks.slice(0, 3).map((code, i) => ({
      id:           `demo-${i + 1}`,
      beat_id:      `beat-0${i + 1}`,
      target_asset: `demo-${projectFlag}-${i + 1}.png`,
      prompt:       code,
      prompt_html:  code,
      response_html: "<p><em>Response to be filled in — run capture-demo.js</em></p>",
      show:         "both",
      zoom_at:      [0.6, 2.5],
      zoom_targets: ["#user-message", "#assistant-message"],
      _source:      `Extracted from ${urlFlag}`,
    }));

    existingConfig = {
      ...existingConfig,
      project:  projectFlag,
      _source:  urlFlag,
      _note:    "Prompts extracted from source URL — review and adjust before running capture-demo.js",
      demos:    suggestedDemos,
    };

    fs.writeFileSync(demoConfigPath, JSON.stringify(existingConfig, null, 2));
    ok(`demo-config.json pre-populated with ${suggestedDemos.length} demo candidate(s)`);
  }

  // ── Summary ─────────────────────────────────────────────────────────────────
  console.log(`\n${"═".repeat(60)}`);
  console.log("✅ Source Brief complete");
  console.log(`\nFiles written:`);
  console.log(`  ${researchPath}`);
  console.log(`  ${jsonPath}`);
  console.log(`  ${ASSETS_DIR}/ (${downloadedImages.length} images, ${sectionScreenshots.length} screenshots)`);
  console.log(`\nNext steps:`);
  console.log(`  1. Claude reads source-research.md and proposes a brief`);
  console.log(`  2. You approve or adjust the brief direction`);
  console.log(`  3. Run: node lib/capture/source-brief.js --url <url> --project <slug>  (already done)`);
  console.log(`  4. Proceed to: /new-reel`);
})();
