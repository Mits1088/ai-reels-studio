#!/usr/bin/env node
/**
 * apply-zoom-hints.js
 *
 * Reads screenshots/zoom-hints.json (produced by capture-demo.js) and writes
 * the zoom_moments into the correct lanes of timeline.json.
 *
 * Supports three target lanes:
 *   --lane demo    (default) — updates demo lane entries matching beat_id
 *   --lane broll             — updates broll lane entries matching beat_id
 *   --lane both              — updates whichever lane has a matching entry
 *
 * Usage:
 *   node lib/capture/apply-zoom-hints.js
 *   node lib/capture/apply-zoom-hints.js --lane broll
 *   node lib/capture/apply-zoom-hints.js --hints path/to/zoom-hints.json
 *   node lib/capture/apply-zoom-hints.js --timeline path/to/timeline.json
 *   node lib/capture/apply-zoom-hints.js --dry-run   (preview changes, don't write)
 *
 * After running, Remotion studio hot-reloads and you can preview the zooms immediately.
 */

const fs   = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "../..");

// ── Args ──────────────────────────────────────────────────────────────────────
const args      = process.argv.slice(2);
const laneFlag  = args.includes("--lane")     ? args[args.indexOf("--lane")     + 1] : "demo";
const hintsFlag = args.includes("--hints")    ? args[args.indexOf("--hints")    + 1] : null;
const tlFlag    = args.includes("--timeline") ? args[args.indexOf("--timeline") + 1] : null;
const dryRun    = args.includes("--dry-run");

const HINTS_PATH = hintsFlag
  ? path.resolve(hintsFlag)
  : path.join(ROOT, "screenshots/zoom-hints.json");

const TIMELINE_PATH = tlFlag
  ? path.resolve(tlFlag)
  : path.join(ROOT, "remotion/public/timeline.json");

// Optional secondary timeline (project output copy)
const projectFlag = args.includes("--project") ? args[args.indexOf("--project") + 1] : null;
const PROJECT_TIMELINE = projectFlag
  ? path.join(ROOT, `projects/${projectFlag}/output/timeline.json`)
  : null;

// ── Load files ────────────────────────────────────────────────────────────────
if (!fs.existsSync(HINTS_PATH)) {
  console.error(`❌ zoom-hints.json not found: ${HINTS_PATH}`);
  console.error("   Run: node lib/capture/capture-demo.js  first.");
  process.exit(1);
}

if (!fs.existsSync(TIMELINE_PATH)) {
  console.error(`❌ timeline.json not found: ${TIMELINE_PATH}`);
  process.exit(1);
}

const hints   = JSON.parse(fs.readFileSync(HINTS_PATH,   "utf8"));
const timeline = JSON.parse(fs.readFileSync(TIMELINE_PATH, "utf8"));

// ── Validate target lane ──────────────────────────────────────────────────────
const validLanes = ["demo", "broll", "support", "both"];
if (!validLanes.includes(laneFlag)) {
  console.error(`❌ Invalid lane "${laneFlag}". Use: demo | broll | support | both`);
  process.exit(1);
}

// ── Apply hints ───────────────────────────────────────────────────────────────
let applied = 0;
let skipped = 0;
const changes = [];

for (const hint of hints) {
  if (!hint.zoom_moments || hint.zoom_moments.length === 0) {
    console.warn(`⚠  ${hint.id}: no zoom_moments in hint (source: ${hint.source}) — skipped`);
    if (hint._note) console.warn(`   Note: ${hint._note}`);
    skipped++;
    continue;
  }

  const targetLanes = laneFlag === "both"
    ? ["demo", "broll", "support"]
    : [laneFlag];

  let matched = false;

  for (const lane of targetLanes) {
    const entries = timeline.lanes[lane] ?? [];
    const entry = entries.find((e) => e.beat_id === hint.beat_id);

    if (!entry) continue;

    const before = JSON.stringify(entry.zoom_moments ?? []);
    entry.zoom_moments = hint.zoom_moments;

    // Update notes to reflect source
    const sourceNote = hint.source === "mock"
      ? "Zoom coords auto-calculated from mock HTML DOM bounding boxes"
      : hint.source === "chatgpt-real"
      ? "Zoom coords auto-calculated from real ChatGPT DOM bounding boxes"
      : "Zoom coords from manual screenshot — verify visually";

    entry.notes = [entry.notes ?? "", sourceNote].filter(Boolean).join(" | ");

    changes.push({
      lane,
      beat_id: hint.beat_id,
      id:      hint.id,
      source:  hint.source,
      before:  JSON.parse(before),
      after:   hint.zoom_moments,
    });

    console.log(`✅ ${lane}/${hint.beat_id} (${hint.id}) — ${hint.zoom_moments.length} zoom moment(s) applied`);
    hint.zoom_moments.forEach((m, i) => {
      console.log(`   Zoom ${i + 1}: at=${m.at}s  x=${m.x}  y=${m.y}  scale=${m.scale}  holdFor=${m.holdFor}s`);
    });

    matched = true;
    applied++;
  }

  if (!matched) {
    console.warn(`⚠  ${hint.id} (${hint.beat_id}): no matching entry in lane "${laneFlag}"`);
    skipped++;
  }
}

// ── Write ─────────────────────────────────────────────────────────────────────
if (dryRun) {
  console.log("\n── Dry run — no files written ─────────────────────────────");
  console.log(JSON.stringify(changes, null, 2));
} else if (applied > 0) {
  fs.writeFileSync(TIMELINE_PATH, JSON.stringify(timeline, null, 2));
  console.log(`\n✅ Written: ${TIMELINE_PATH}`);

  // Sync to project output copy if --project was specified and file exists
  if (PROJECT_TIMELINE && fs.existsSync(PROJECT_TIMELINE)) {
    fs.writeFileSync(PROJECT_TIMELINE, JSON.stringify(timeline, null, 2));
    console.log(`✅ Synced:  ${PROJECT_TIMELINE}`);
  }
} else {
  console.log("\nNothing to write — no entries were updated.");
}

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n── Summary ──────────────────────────────────────────────────`);
console.log(`   Applied : ${applied}`);
console.log(`   Skipped : ${skipped}`);

if (applied > 0 && !dryRun) {
  console.log(`\nNext: check Remotion studio — zoom changes hot-reload immediately.`);
  console.log(`      If coords look off, re-run capture-demo.js or adjust manually in timeline.json.`);
}

if (skipped > 0) {
  console.log(`\n⚠  Skipped entries may need manual zoom coordinates.`);
  console.log(`   For manual screenshots: share them with Claude → zoom coords are calculated`);
  console.log(`   using frame_x = image_x, frame_y = image_y × 0.57 (contain+top formula)`);
}
