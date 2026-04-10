#!/usr/bin/env node
/**
 * capture-x-video.js
 *
 * Downloads video from an X/Twitter post using authenticated session cookies.
 * Credentials come from .env (AUTH_TOKEN, CT0) — no Playwright storageState file.
 *
 * Approach:
 *   1. Launch Playwright with X session cookies injected
 *   2. Navigate to the tweet URL
 *   3. Intercept network requests to capture the video blob URL (.mp4)
 *   4. Download the highest-quality video variant
 *   5. Re-encode for Remotion (libx264, yuv420p, 30fps, -g 1, faststart, audio track)
 *   6. Copy to remotion/public/
 *
 * Usage:
 *   node lib/capture/capture-x-video.js --url https://x.com/user/status/123 --out demo-stitch.mp4
 *   node lib/capture/capture-x-video.js --url https://x.com/user/status/123 --out demo-stitch.mp4 --project google-stitch
 *   node lib/capture/capture-x-video.js --list x-sources.json
 *
 * Flags:
 *   --url       Single tweet URL
 *   --out       Output filename (placed in remotion/public/)
 *   --project   Project slug — also saves to projects/<slug>/assets/
 *   --list      JSON file with array of { url, out, beat_id } entries
 *   --no-reencode  Skip FFmpeg re-encode (keep original mp4)
 */

require("dotenv").config();
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");
const { execSync } = require("child_process");

const ROOT = path.resolve(__dirname, "../..");
const PUBDIR = path.join(ROOT, "remotion/public");

// ── Parse args ───────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
}
const hasFlag = (name) => args.includes(`--${name}`);

const singleUrl = getArg("url");
const singleOut = getArg("out");
const projectSlug = getArg("project");
const listFile = getArg("list");
const skipReencode = hasFlag("no-reencode");

// ── Validate credentials ─────────────────────────────────────────────────────
const AUTH_TOKEN = process.env.AUTH_TOKEN;
const CT0 = process.env.CT0;

if (!AUTH_TOKEN || !CT0) {
  console.error("❌ Missing AUTH_TOKEN or CT0 in .env");
  console.error("   Copy your X session cookies from browser DevTools:");
  console.error("   Application > Cookies > x.com > auth_token and ct0");
  process.exit(1);
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function log(msg) { console.log(msg); }
function ok(msg) { console.log(`  ✅ ${msg}`); }
function warn(msg) { console.warn(`  ⚠  ${msg}`); }
function fail(msg) { console.error(`  ❌ ${msg}`); }

function normalizeUrl(url) {
  // Accept twitter.com or x.com, normalize to x.com
  return url.replace("twitter.com", "x.com");
}

function extractTweetId(url) {
  const match = url.match(/status\/(\d+)/);
  return match ? match[1] : null;
}

/** Download a URL to a local file path */
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const client = url.startsWith("https") ? https : http;
    client.get(url, { headers: { "User-Agent": "Mozilla/5.0" } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        // Follow redirect
        downloadFile(res.headers.location, dest).then(resolve).catch(reject);
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        return;
      }
      res.pipe(file);
      file.on("finish", () => { file.close(); resolve(); });
    }).on("error", reject);
  });
}

/** Re-encode video for Remotion compliance */
function reencodeForRemotion(input, output) {
  // Check if source has audio
  let hasAudio = false;
  try {
    const probe = execSync(
      `ffprobe -v quiet -select_streams a -show_entries stream=codec_type -of csv=p=0 "${input}"`,
      { encoding: "utf8" }
    ).trim();
    hasAudio = probe.includes("audio");
  } catch (_) {}

  const audioArgs = hasAudio
    ? "-c:a aac -b:a 128k"
    : '-f lavfi -i anullsrc=r=44100:cl=mono -shortest -c:a aac -b:a 128k';

  // Need different input syntax when adding silent audio
  const inputArgs = hasAudio
    ? `"${input}"`
    : `"${input}" -f lavfi -i anullsrc=r=44100:cl=mono`;

  const cmd = `ffmpeg -y -i ${inputArgs} -r 30 -c:v libx264 -profile:v high -pix_fmt yuv420p -g 1 -movflags +faststart ${hasAudio ? "-c:a aac -b:a 128k" : "-c:a aac -b:a 128k -shortest"} "${output}"`;

  try {
    execSync(cmd, { stdio: "pipe" });
    return true;
  } catch (e) {
    fail(`FFmpeg re-encode failed: ${e.message}`);
    return false;
  }
}

/** Use X API to get video variants (highest quality mp4) */
async function getVideoUrlViaApi(tweetId) {
  const apiUrl = `https://api.x.com/graphql/B9_KmbkLhXt6jRwGjJrweg/TweetResultByRestId`;
  const variables = JSON.stringify({
    tweetId,
    withCommunity: false,
    includePromotedContent: false,
    withVoice: false,
  });
  const features = JSON.stringify({
    creator_subscriptions_tweet_preview_api_enabled: true,
    c9s_tweet_anatomy_moderator_badge_enabled: true,
    tweetypie_unmention_optimization_enabled: true,
    responsive_web_edit_tweet_api_enabled: true,
    graphql_is_translatable_rweb_tweet_is_translatable_enabled: true,
    view_counts_everywhere_api_enabled: true,
    longform_notetweets_consumption_enabled: true,
    responsive_web_twitter_article_tweet_consumption_enabled: true,
    tweet_awards_web_tipping_enabled: false,
    responsive_web_home_pinned_timelines_enabled: true,
    freedom_of_speech_not_reach_fetch_enabled: true,
    standardized_nudges_misinfo: true,
    tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled: true,
    rweb_video_timestamps_enabled: true,
    longform_notetweets_rich_text_read_enabled: true,
    longform_notetweets_inline_media_enabled: true,
    responsive_web_graphql_exclude_directive_enabled: true,
    verified_phone_label_enabled: false,
    responsive_web_graphql_skip_user_profile_image_extensions_enabled: false,
    responsive_web_graphql_timeline_navigation_enabled: true,
    responsive_web_enhance_cards_enabled: false,
  });

  const params = new URLSearchParams({ variables, features });
  const fullUrl = `${apiUrl}?${params}`;

  try {
    const res = await fetch(fullUrl, {
      headers: {
        Authorization: "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        Cookie: `auth_token=${AUTH_TOKEN}; ct0=${CT0}`,
        "x-csrf-token": CT0,
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      warn(`API returned ${res.status} — will fall back to page scrape`);
      return null;
    }

    const data = await res.json();
    const result = data?.data?.tweetResult?.result;
    const legacy = result?.legacy || result?.tweet?.legacy;
    const media = legacy?.extended_entities?.media || legacy?.entities?.media || [];
    const videoMedia = media.find((m) => m.type === "video" || m.type === "animated_gif");

    if (!videoMedia?.video_info?.variants) {
      warn("Tweet has no video media");
      return null;
    }

    // Pick highest bitrate mp4 variant
    const mp4s = videoMedia.video_info.variants
      .filter((v) => v.content_type === "video/mp4")
      .sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));

    if (mp4s.length === 0) {
      warn("No mp4 variants found");
      return null;
    }

    return mp4s[0].url;
  } catch (e) {
    warn(`API fetch failed: ${e.message}`);
    return null;
  }
}

/** Fallback: use Playwright to intercept video network requests */
async function getVideoUrlViaPage(tweetUrl) {
  log("  Launching browser for page-level video capture...");

  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox"],
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  });

  // Inject X cookies
  await context.addCookies([
    { name: "auth_token", value: AUTH_TOKEN, domain: ".x.com", path: "/", secure: true, httpOnly: true, sameSite: "None" },
    { name: "ct0", value: CT0, domain: ".x.com", path: "/", secure: true, httpOnly: false, sameSite: "Lax" },
  ]);

  const page = await context.newPage();
  const videoUrls = [];

  // Intercept video requests — collect all mp4 URLs from video.twimg.com
  page.on("response", async (response) => {
    const url = response.url();
    if (url.includes("video.twimg.com") && url.includes(".mp4")) {
      videoUrls.push(url);
    }
  });

  try {
    await page.goto(tweetUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
    await page.waitForTimeout(3000);

    // Try multiple play triggers
    await page.click('video', { timeout: 3000 }).catch(() => {});
    await page.click('[data-testid="playButton"]', { timeout: 2000 }).catch(() => {});
    await page.click('[data-testid="videoPlayer"]', { timeout: 2000 }).catch(() => {});
    await page.click('[aria-label="Play"]', { timeout: 2000 }).catch(() => {});

    // Wait for video network requests
    await page.waitForTimeout(6000);

    // If still no video, try scrolling to trigger lazy load
    if (videoUrls.length === 0) {
      await page.evaluate(() => window.scrollBy(0, 300));
      await page.waitForTimeout(3000);
    }
  } catch (e) {
    warn(`Page navigation issue: ${e.message}`);
  }

  await browser.close();

  if (videoUrls.length === 0) return null;

  // Pick the highest quality variant — X serves multiple resolutions
  // Higher resolution URLs tend to have larger dimension tags (e.g. /vid/avc1/1280x720/)
  const sorted = [...new Set(videoUrls)].sort((a, b) => {
    const dimA = a.match(/(\d+)x(\d+)/);
    const dimB = b.match(/(\d+)x(\d+)/);
    const pixA = dimA ? parseInt(dimA[1]) * parseInt(dimA[2]) : 0;
    const pixB = dimB ? parseInt(dimB[1]) * parseInt(dimB[2]) : 0;
    return pixB - pixA;
  });

  return sorted[0];
}

// ── Main capture function ────────────────────────────────────────────────────
async function captureOne({ url, out, beat_id }) {
  const tweetUrl = normalizeUrl(url);
  const tweetId = extractTweetId(tweetUrl);

  log(`\n${"═".repeat(60)}`);
  log(`Capturing: ${tweetUrl}`);
  log(`  Tweet ID: ${tweetId}`);
  log(`  Output:   ${out}`);
  if (beat_id) log(`  Beat:     ${beat_id}`);
  log("═".repeat(60));

  if (!tweetId) {
    fail("Could not extract tweet ID from URL");
    return false;
  }

  // Strategy 1: Page scrape via Playwright (reliable — no rotating GraphQL hashes)
  log("  Capturing via Playwright page scrape...");
  let videoUrl = await getVideoUrlViaPage(tweetUrl);

  // Strategy 2: X GraphQL API (fast but hashes rotate — fallback)
  if (!videoUrl) {
    log("  Page scrape failed, trying X API...");
    videoUrl = await getVideoUrlViaApi(tweetId);
  }

  if (!videoUrl) {
    fail("Could not find video URL via API or page scrape");
    fail("The tweet may not contain a video, or the session may have expired.");
    fail("To refresh: grab new auth_token and ct0 from browser DevTools > Cookies > x.com");
    return false;
  }

  ok(`Video URL found: ${videoUrl.substring(0, 80)}...`);

  // Download to temp file
  const tmpDir = path.join(ROOT, "screenshots", "_x_raw");
  fs.mkdirSync(tmpDir, { recursive: true });
  const rawPath = path.join(tmpDir, `${tweetId}_raw.mp4`);

  log("  Downloading...");
  try {
    await downloadFile(videoUrl, rawPath);
    const size = fs.statSync(rawPath).size;
    ok(`Downloaded: ${(size / 1024 / 1024).toFixed(1)}MB`);
  } catch (e) {
    fail(`Download failed: ${e.message}`);
    return false;
  }

  // Re-encode for Remotion
  const outPath = path.join(PUBDIR, out);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });

  if (skipReencode) {
    fs.copyFileSync(rawPath, outPath);
    ok(`Copied (no re-encode): ${out}`);
  } else {
    log("  Re-encoding for Remotion (libx264, 30fps, -g 1)...");
    if (reencodeForRemotion(rawPath, outPath)) {
      ok(`Encoded: ${out}`);
    } else {
      // Fall back to raw copy
      fs.copyFileSync(rawPath, outPath);
      warn(`Using raw file (re-encode failed): ${out}`);
    }
  }

  // Also save to project assets if --project specified
  if (projectSlug) {
    const projPath = path.join(ROOT, "projects", projectSlug, "assets", out);
    fs.mkdirSync(path.dirname(projPath), { recursive: true });
    fs.copyFileSync(outPath, projPath);
    ok(`Project copy: projects/${projectSlug}/assets/${out}`);
  }

  // Probe output for validation
  try {
    const probe = execSync(
      `ffprobe -v quiet -show_entries stream=codec_name,r_frame_rate,pix_fmt,duration -of json "${outPath}"`,
      { encoding: "utf8" }
    );
    const info = JSON.parse(probe);
    const video = info.streams?.find((s) => s.codec_name === "h264");
    if (video) {
      ok(`Validated: h264 ${video.pix_fmt} ${video.r_frame_rate}fps ${parseFloat(video.duration).toFixed(1)}s`);
    }
  } catch (_) {
    warn("Could not probe output — check manually with ffprobe");
  }

  return true;
}

// ── Main ─────────────────────────────────────────────────────────────────────
(async () => {
  fs.mkdirSync(PUBDIR, { recursive: true });

  let jobs = [];

  if (listFile) {
    const listPath = path.resolve(listFile);
    if (!fs.existsSync(listPath)) {
      fail(`List file not found: ${listPath}`);
      process.exit(1);
    }
    jobs = JSON.parse(fs.readFileSync(listPath, "utf8"));
    log(`Loaded ${jobs.length} jobs from ${listFile}`);
  } else if (singleUrl && singleOut) {
    jobs = [{ url: singleUrl, out: singleOut }];
  } else {
    console.error("Usage:");
    console.error("  node lib/capture/capture-x-video.js --url <tweet-url> --out <filename.mp4>");
    console.error("  node lib/capture/capture-x-video.js --list <x-sources.json>");
    process.exit(1);
  }

  let passed = 0;
  let failed = 0;

  for (const job of jobs) {
    const success = await captureOne(job);
    if (success) passed++;
    else failed++;
  }

  log(`\n${"═".repeat(60)}`);
  log(`Done: ${passed} captured, ${failed} failed`);
  if (passed > 0) {
    log(`Videos in: ${PUBDIR}`);
  }
  if (failed > 0) {
    log("Check failed URLs — session may need refresh or tweets may not have video.");
  }
})();
