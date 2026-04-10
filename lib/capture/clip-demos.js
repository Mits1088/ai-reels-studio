#!/usr/bin/env node
/**
 * clip-demos.js
 *
 * Clips and speed-adjusts the raw demo recordings.
 * - Typing portion: normal speed
 * - Response portion: sped up (responseSpeed x)
 * - Output: trimmed mp4 ready for Remotion
 *
 * Usage: node lib/capture/clip-demos.js --output projects/<slug>/screenshots
 */

const { execSync } = require("child_process");
const fs   = require("fs");
const path = require("path");

const ROOT   = path.resolve(__dirname, "../..");
const PUBDIR = path.join(ROOT, "remotion/public");

const args      = process.argv.slice(2);
const customOut = args.includes("--output") ? args[args.indexOf("--output") + 1] : path.join(ROOT, "screenshots");
const OUTDIR    = path.resolve(customOut);

// Edit plan for each demo
// With the new recording approach (body fast-typed, START_TRIM_S=4):
//   - The trimmed mp4 starts when the cursor is positioned, body text visible
//   - typingEnd: seconds from trimmed clip start when code finishes + submit pressed
//   - responseEnd: seconds from trimmed clip start to stop capturing response
//   - responseSpeed: playback multiplier for the response section
//
// New recording timing estimate (after 4s trim):
//   0.0–0.8s  = cursor pause + viewer sees body text
//   0.8–2.5s  = code typed slowly (7–10 chars × 120ms ≈ 1-1.5s)
//   2.5–3.2s  = post-type pause + Enter
//   3.2–5s    = ChatGPT thinking
//   5–14s     = response streaming
//
// AFTER re-recording, check frames/  to verify and fine-tune these values.
const EDITS = [
  {
    id:            "demo-human",
    input:         path.join(OUTDIR, "demo-human-response.mp4"),
    output:        path.join(OUTDIR, "demo-human-clipped.mp4"),
    publicAsset:   "demo-chatgpt-human.mp4",
    typingEnd:     3.5,  // body visible → /human typed → submitted
    responseEnd:   10,   // 6.5s of response at 1.5x = ~4.3s video time
    responseSpeed: 1.5,
  },
  {
    id:            "demo-x10think",
    input:         path.join(OUTDIR, "demo-x10think-response.mp4"),
    output:        path.join(OUTDIR, "demo-x10think-clipped.mp4"),
    publicAsset:   "demo-chatgpt-x10think.mp4",
    typingEnd:     3.5,  // body visible → X10think appended → submitted
    responseEnd:   10,   // 6.5s of response at 1.5x = ~4.3s video time
    responseSpeed: 1.5,
  },
  {
    id:            "demo-killcritic",
    input:         path.join(OUTDIR, "demo-killcritic-response.mp4"),
    output:        path.join(OUTDIR, "demo-killcritic-clipped.mp4"),
    publicAsset:   "demo-chatgpt-killcritic.mp4",
    typingEnd:     3.5,  // body visible → killcritic appended → submitted
    responseEnd:   10,   // 6.5s of response at 1.5x = ~4.3s video time
    responseSpeed: 1.5,
  },
  {
    id:            "demo-alt3",
    input:         path.join(OUTDIR, "demo-alt3-response.mp4"),
    output:        path.join(OUTDIR, "demo-alt3-clipped.mp4"),
    publicAsset:   "demo-chatgpt-alt3.mp4",
    typingEnd:     3.5,  // body visible → alt3 appended → submitted
    responseEnd:   10,   // 6.5s of response at 1.5x = ~4.3s video time
    responseSpeed: 1.5,
  },
];

function ok(msg)   { console.log(`✅ ${msg}`); }
function fail(msg) { console.error(`❌ ${msg}`); }

for (const edit of EDITS) {
  console.log(`\nClipping: ${edit.id}`);
  console.log(`  Typing 0–${edit.typingEnd}s (1x) + Response ${edit.typingEnd}–${edit.responseEnd}s (${edit.responseSpeed}x)`);

  if (!fs.existsSync(edit.input)) {
    fail(`Input not found: ${edit.input}`);
    continue;
  }

  const speedPts = (1 / edit.responseSpeed).toFixed(4);

  // filter_complex:
  //   v1 = 0 → typingEnd at normal speed
  //   v2 = typingEnd → responseEnd sped up
  //   concat v1 + v2
  const filter = [
    `[0:v]trim=start=0:end=${edit.typingEnd},setpts=PTS-STARTPTS[v1]`,
    `[0:v]trim=start=${edit.typingEnd}:end=${edit.responseEnd},setpts=${speedPts}*(PTS-STARTPTS)[v2]`,
    `[v1][v2]concat=n=2:v=1:a=0[outv]`,
  ].join(";");

  try {
    execSync(
      `ffmpeg -y -i "${edit.input}" -filter_complex "${filter}" -map "[outv]" -c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p "${edit.output}"`,
      { stdio: "pipe" }
    );

    // Check output duration
    const dur = execSync(
      `ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${edit.output}"`,
      { encoding: "utf8" }
    ).trim();

    ok(`${edit.output} — ${parseFloat(dur).toFixed(1)}s`);

    // Copy to remotion/public
    const pubPath = path.join(PUBDIR, edit.publicAsset);
    fs.copyFileSync(edit.output, pubPath);
    ok(`Remotion public: ${edit.publicAsset}`);
  } catch (e) {
    fail(`FFmpeg failed for ${edit.id}: ${e.message}`);
  }
}

console.log("\n✅ Done. Review the *-clipped.mp4 files, then adjust typingEnd/responseEnd in this script if needed.");
