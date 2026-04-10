#!/usr/bin/env node
/**
 * extract-frames.js
 *
 * Extract PNG frames from broll videos at specific timestamps using ffmpeg.
 * Use this to get screenshots for zoom coordinate calibration.
 *
 * Usage:
 *   node lib/capture/extract-frames.js
 *   node lib/capture/extract-frames.js --config lib/capture/broll-timestamps.json
 *   node lib/capture/extract-frames.js --video broll-el10.mp4 --times 0.8,3.8
 *
 * Output: screenshots/<videoname>_t<time>.png
 * Next step: share those PNGs with Claude → zoom coords are calculated → timeline.json updated
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");
const BROLL_DIR = path.join(ROOT, "remotion/public");
const OUT_DIR = path.join(ROOT, "screenshots");

// ── Parse args ────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const configFlag = args.indexOf("--config");
const videoFlag = args.indexOf("--video");
const timesFlag = args.indexOf("--times");

let config = {};

if (videoFlag !== -1 && timesFlag !== -1) {
  const video = args[videoFlag + 1];
  const times = args[timesFlag + 1].split(",").map(Number);
  config[video] = times;
} else {
  const configPath =
    configFlag !== -1
      ? path.resolve(args[configFlag + 1])
      : path.join(__dirname, "broll-timestamps.json");

  if (!fs.existsSync(configPath)) {
    console.error(`❌ Config not found: ${configPath}`);
    console.error(
      "   Create broll-timestamps.json or pass --video <file> --times <t1,t2>"
    );
    process.exit(1);
  }
  config = JSON.parse(fs.readFileSync(configPath, "utf8"));
}

// ── Extract ───────────────────────────────────────────────────────────────────
fs.mkdirSync(OUT_DIR, { recursive: true });

let extracted = 0;
let failed = 0;
const results = [];

for (const [filename, timestamps] of Object.entries(config)) {
  const inputPath = path.join(BROLL_DIR, filename);
  const base = path.basename(filename, path.extname(filename));

  if (!fs.existsSync(inputPath)) {
    console.warn(`⚠  Not found (skipping): ${inputPath}`);
    failed++;
    continue;
  }

  for (const ts of timestamps) {
    const label = ts.toFixed(1).replace(".", "s");
    const outName = `${base}_t${label}.png`;
    const outPath = path.join(OUT_DIR, outName);

    try {
      // -ss before -i = fast seek (keyframe), accurate enough for calibration
      execSync(
        `ffmpeg -ss ${ts} -i "${inputPath}" -vframes 1 -q:v 2 "${outPath}" -y`,
        { stdio: "pipe" }
      );
      console.log(`✅ ${outName}`);
      results.push({ file: filename, timestamp: ts, screenshot: outPath });
      extracted++;
    } catch (e) {
      console.error(`❌ Failed ${outName}: ${e.stderr?.toString().split("\n").pop() ?? e.message}`);
      failed++;
    }
  }
}

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n── Summary ────────────────────────────────`);
console.log(`   Extracted : ${extracted}`);
console.log(`   Failed    : ${failed}`);
console.log(`   Output    : ${OUT_DIR}`);
console.log(`\nNext steps:`);
console.log(`  1. Open the screenshots/ folder and review each frame`);
console.log(`  2. Share them with Claude — zoom coordinates will be calculated`);
console.log(`     using the contain+top formula: frame_x = image_x, frame_y = image_y × 0.57`);
console.log(`  3. Claude updates timeline.json broll zoom_moments`);

// Write a manifest so Claude can find the files easily
const manifestPath = path.join(OUT_DIR, "extract-manifest.json");
fs.writeFileSync(manifestPath, JSON.stringify({ extracted: results, config }, null, 2));
console.log(`\nManifest written: ${manifestPath}`);
