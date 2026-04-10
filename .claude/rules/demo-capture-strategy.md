---
description: How to capture demo screenshots for reels — fallback chain when live sites block automation
globs: ["lib/capture/**", "**/demo-config.json", "**/assets-needed.md"]
---

# Demo Capture Strategy

## The Problem

Live AI product sites (ChatGPT, Claude, Gemini, etc.) actively block automated browsers.
Common blocks: login walls, CAPTCHA, rate limits, bot detection, access denied.

Never assume the live site will be accessible. Always plan for fallbacks.

## The 4-Stage Fallback Chain

### Stage 0 — X/Twitter video capture (best real footage)

Many AI products post official demo videos on X. These are often the highest-quality
demo footage available — real product recordings, polished by the product team.

**How it works:**
- Credentials are env-var driven: `AUTH_TOKEN` and `CT0` in `.env`
- No Playwright storageState file — cookies injected at runtime
- Two strategies: X GraphQL API first (fast, gets highest bitrate mp4), page scrape fallback
- Videos are auto re-encoded for Remotion (libx264, 30fps, -g 1, faststart, audio track)

**Usage:**
```bash
# Single tweet
node lib/capture/capture-x-video.js --url https://x.com/user/status/123 --out demo-stitch.mp4

# Multiple tweets (batch)
node lib/capture/capture-x-video.js --list projects/<slug>/x-sources.json

# With project copy
node lib/capture/capture-x-video.js --url <url> --out demo.mp4 --project <slug>
```

**Batch file format** (`x-sources.json`):
```json
[
  { "url": "https://x.com/GoogleLabs/status/123", "out": "demo-stitch-canvas.mp4", "beat_id": "beat-03a" },
  { "url": "https://x.com/GoogleLabs/status/456", "out": "demo-stitch-export.mp4", "beat_id": "beat-04" }
]
```

**When to use:**
- Product team posted a demo video on their official X account
- A researcher/reviewer posted a clear screen recording on X
- The tweet shows a real product interaction that matches the reel's narration

**Session refresh:**
- `auth_token` and `ct0` expire when X rotates the session (logout, password change)
- Grab fresh values from browser DevTools > Application > Cookies > x.com
- Update `.env` — no restart needed

**Stage 0 does NOT replace Stage 3.** The X video is source footage that may need
trimming, speed adjustment, or cropping. The mock is still the safe fallback when
no X demo exists or the X video doesn't match the narration.

---

### Stage 1 — Real site via Playwright

Playwright navigates to the live product URL, types the prompt, waits for the response,
screenshots at key moments, and extracts DOM bounding boxes for automatic zoom coordinate
calculation.

**Blocked indicators** (script detects these automatically):
- URL contains `/auth/`, `/login`, `auth0`
- Page body contains "captcha", "verify you are human", "unusual traffic"
- Page body contains "access denied", "403 forbidden", "sign in to continue"
- Navigation timeout (>15s)

If any of these fire → skip to Stage 2.

### Stage 2 — Manual screenshots from user

User supplies their own clear screenshots of the demo.

Drop files into: `screenshots/manual/<demo-id>-prompt.png` and `<demo-id>-response.png`

The script will detect them and use them. Zoom coordinates cannot be auto-calculated
from manual screenshots — the user should share them with Claude after this step
so zoom_moments can be set manually using the contain+top formula.

### Stage 3 — Mock HTML (always works)

Load `lib/capture/templates/chatgpt-mock.html` in a headless browser.
Inject the prompt text and response text from `demo-config.json`.
Take two screenshots (prompt-only, then with response).
Auto-calculate zoom coordinates from DOM bounding boxes.
Copy the production screenshot to `remotion/public/` for immediate use in the reel.

**The mock is the safe default.** When in doubt, go straight to Stage 3:
```
node lib/capture/capture-demo.js --stage 3
```

## When to Use Each Stage

| Situation | Stage |
|---|---|
| Product team posted demo video on X | 0 (real footage, best quality) |
| Clear demo recording found on X from reviewer | 0 |
| Site is accessible and user is logged in | 1 |
| User recorded their own screen | 2 |
| Site is blocked, no recording available | 3 |
| Scripted CI / unattended run | 3 (use --no-interactive) |
| Single clean demo needed quickly | 3 (fastest, most reliable) |

## The Mock HTML

### Premium Claude Mock (preferred for all Claude demos)

`lib/capture/templates/claude-premium-mock.html` is the standard template for Claude.ai demos.

- Uses the real Claude sparkle logo: `lib/capture/templates/claude-logo.png` (source: `Images/LogosClaudeIcon_orange.png`)
- Design system: Source Serif 4 headings, Inter body, `#FAF9F5` background, `#D97757` accent
- User name: "Mits" (edit in HTML to change)
- States via URL hash: `#homepage` (greeting + input), `#typing` (user types prompt), `#activate` (new chat + skill auto-activation banner)
- Viewport: 540×960 (portrait 9:16) for Playwright `recordVideo`
- Playwright outputs webm — convert to mp4 with FFmpeg before Remotion import
- No browser chrome, bookmarks, or personal data beyond the approved name

**Always inspect frames after capture.** Extract at least one frame from each captured clip and visually verify: no personal data, no browser chrome, content matches the narration it will accompany.

### ChatGPT Mock (for ChatGPT demos)

`lib/capture/templates/chatgpt-mock.html` replicates the ChatGPT UI.

- Accepts content via `window.applyContent({ prompt, response, show, title, model })`
- `show: "prompt"` — user message only (no response visible)
- `show: "both"` — user message + assistant response visible
- Viewport: 1280×720 (landscape, 16:9)
- Output matches the visual style of the demo slides used in the reel

To customise for a different product (Claude, Gemini, etc.), duplicate the template
and adjust brand colours, fonts, and layout. Keep the `#user-message` and
`#assistant-message` element IDs — the capture script uses them for bounding boxes.

## Zoom Coordinate Output

After any successful capture, `screenshots/zoom-hints.json` is written:

```json
[
  {
    "id": "el10",
    "beat_id": "beat-04",
    "source": "mock",
    "zoom_moments": [
      { "at": 0.6, "x": 72, "y": 19, "scale": 2.4, "holdFor": 2.0 },
      { "at": 3.0, "x": 50, "y": 31, "scale": 2.0, "holdFor": 2.0 }
    ]
  }
]
```

These values are already adjusted for the `contain+top` letterbox formula and
can be pasted directly into the `demo` lane of `timeline.json`.

## Config Files

- `lib/capture/demo-config.json` — defines each demo: prompt, response, beat_id, target_asset
- `lib/capture/broll-timestamps.json` — timestamps for extracting frames from existing broll videos

## Key Rules

1. **Always have Stage 3 ready** — the mock is the production fallback, not a last resort.
   Prepare `demo-config.json` with prompt and response text before any capture run.

2. **Stage 2 requires clear, unobstructed screenshots** — if the user provides screenshots
   that have notifications, overlays, or UI chrome obscuring the content, ask for a clean one.

3. **Zoom coords from Stage 1/3 are auto-calculated** — use them directly in timeline.json.
   Zoom coords from Stage 2 (manual) require Claude review of the screenshot.

4. **Update the mock for each product** — if a reel covers Claude, Gemini, Perplexity etc.,
   create a matching mock template in `lib/capture/templates/`. Same fallback chain applies.

5. **Never record prompts or responses that could expose private user data** — use
   neutral, clearly illustrative examples that match the reel's educational purpose.
