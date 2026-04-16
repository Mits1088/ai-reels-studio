#!/usr/bin/env node
/**
 * generate-timed-captions.mjs
 *
 * Converts audio/voice.json (ElevenLabs word-level transcript) into
 * audio/captions-v2.json — caption pages with per-word timing tokens.
 *
 * The output is backwards-compatible with the existing captions lane
 * in timeline.json. Each entry has:
 *   - text:   full page text (same as before)
 *   - start:  page start in seconds
 *   - end:    page end in seconds
 *   - beat_id: placeholder (same as before)
 *   - tokens: [{text, fromMs, toMs}] — NEW: word-level timing for karaoke captions
 *
 * Usage:
 *   node lib/generate-timed-captions.mjs projects/<slug>/audio/voice.json
 *
 * Output:
 *   projects/<slug>/audio/captions-v2.json
 *
 * To use in a project's timeline.json, replace the captions lane entries
 * with the contents of captions-v2.json (or run caption-polish which will
 * call this automatically when voice.json has word-level data).
 *
 * Dependencies: @remotion/captions (installed in remotion/node_modules)
 */

import { createReadStream, writeFileSync, existsSync } from "fs";
import { readFile } from "fs/promises";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const remotionRoot = join(__dirname, "..", "remotion", "node_modules");

// Load @remotion/captions from the remotion node_modules
const captionsPath = join(remotionRoot, "@remotion", "captions", "dist", "index.js");

if (!existsSync(captionsPath)) {
  console.error("ERROR: @remotion/captions not found. Run: cd remotion && npm install");
  process.exit(1);
}

// Windows requires file:// URL for dynamic ESM import of absolute paths
const captionsUrl = new URL(`file:///${captionsPath.replace(/\\/g, "/")}`).href;
const { createTikTokStyleCaptions } = await import(captionsUrl);

// ── CLI arg ───────────────────────────────────────────────────────────

const voicePath = process.argv[2];
if (!voicePath) {
  console.error("Usage: node lib/generate-timed-captions.mjs projects/<slug>/audio/voice.json");
  process.exit(1);
}

const resolvedVoicePath = resolve(process.cwd(), voicePath);
if (!existsSync(resolvedVoicePath)) {
  console.error(`ERROR: File not found: ${resolvedVoicePath}`);
  process.exit(1);
}

// ── Read voice.json ───────────────────────────────────────────────────

const voiceData = JSON.parse(await readFile(resolvedVoicePath, "utf8"));

// Flatten all words from all sentences into a flat Caption[] array
// voice.json format: { sentences: [{ words: [{ word, start, end }] }] }
const captions = [];

if (voiceData.sentences) {
  // ElevenLabs sentence+word format (our standard voice.json)
  for (const sentence of voiceData.sentences) {
    for (let i = 0; i < sentence.words.length; i++) {
      const w = sentence.words[i];
      const nextW = sentence.words[i + 1];
      const isFirst = captions.length === 0;
      captions.push({
        text: isFirst ? w.word : ` ${w.word}`,
        startMs: Math.round(w.start * 1000),
        endMs: Math.round((nextW ? nextW.start : w.end) * 1000),
        confidence: null,
        timestampMs: Math.round(((w.start + w.end) / 2) * 1000),
      });
    }
  }
} else if (Array.isArray(voiceData)) {
  // Flat array format (some older voice.json files)
  for (const entry of voiceData) {
    const words = (entry.text || "").split(" ").filter(Boolean);
    const dur = (entry.end - entry.start) / words.length;
    let t = entry.start;
    for (const word of words) {
      captions.push({
        text: ` ${word}`,
        startMs: Math.round(t * 1000),
        endMs: Math.round((t + dur) * 1000),
        confidence: null,
        timestampMs: Math.round((t + dur / 2) * 1000),
      });
      t += dur;
    }
  }
} else {
  console.error("ERROR: Unrecognised voice.json format. Expected { sentences: [...] } or array.");
  process.exit(1);
}

if (captions.length === 0) {
  console.error("ERROR: No words found in voice.json");
  process.exit(1);
}

// ── Build TikTok-style pages ──────────────────────────────────────────

// combineTokensWithinMilliseconds: max chunk duration before starting a new page.
// 2000ms = 2s max per caption page — readable on mobile, syncs naturally to phrases.
const { pages } = createTikTokStyleCaptions({
  captions,
  combineTokensWithinMilliseconds: 2000,
});

// ── Convert to our timeline captions format ───────────────────────────

const timedCaptions = pages.map((page, i) => ({
  beat_id: "",
  text: page.text.trim(),
  start: page.startMs / 1000,
  end: (page.startMs + page.durationMs) / 1000,
  tokens: page.tokens.map((t) => ({
    text: t.text.trim(),
    fromMs: t.fromMs,
    toMs: t.toMs,
  })),
}));

// ── Write output ──────────────────────────────────────────────────────

const outputPath = resolvedVoicePath.replace("voice.json", "captions-v2.json");
writeFileSync(outputPath, JSON.stringify(timedCaptions, null, 2));

console.log(`✓ ${timedCaptions.length} caption pages → ${outputPath}`);
console.log(`  Total words: ${captions.length}`);
console.log(`  Duration: ${(timedCaptions[timedCaptions.length - 1]?.end ?? 0).toFixed(2)}s`);
console.log(`\nTo activate: copy captions-v2.json entries into your timeline.json captions lane.`);
console.log(`Caption.tsx will auto-detect tokens and switch to karaoke mode.`);
