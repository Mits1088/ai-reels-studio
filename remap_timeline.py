import json

with open(r'D:\Reel generation\remotion\public\timeline.json', 'r', encoding='utf-8') as f:
    tl = json.load(f)

tl['total_duration'] = 42.07

tl['lanes']['avatar'] = [
    {"_comment": "Hook: split-screen", "beat_id": "beat-01a", "start": 0, "end": 3.30, "asset": "avatar.mp4", "layout": "split-screen"},
    {"_comment": "Keyword enumeration: full-screen, covered by guided-demo at z12", "beat_id": "beat-01b-02", "start": 3.30, "end": 8.20, "asset": "avatar.mp4", "layout": "full-screen", "bgColor": "#F5F0E8"},
    {"_comment": "Demo section: covered by guided-demo entries", "beat_id": "beat-03-07", "start": 8.20, "end": 35.45, "asset": "avatar.mp4", "layout": "full-screen", "bgColor": "#F5F0E8"},
    {"_comment": "Cost beat: full-screen, white background", "beat_id": "beat-08", "start": 35.45, "end": 38.90, "asset": "avatar.mp4", "layout": "full-screen", "bgColor": "#FFFFFF"},
    {"_comment": "CTA: full-screen, dark background", "beat_id": "beat-09", "start": 38.90, "end": 42.07, "asset": "avatar.mp4", "layout": "full-screen", "bgColor": "#1A1A1A"}
]

tl['lanes']['demo'] = [
    {
        "_comment": "Hook b-roll in top 40%",
        "beat_id": "beat-01a-broll", "start": 0, "end": 3.30,
        "asset": "hook-broll.mp4", "playbackRate": 1
    },
    {
        "_comment": "GitHub skills README scroll. Duration rescaled 6.67s->4.90s; pan/highlight at values rescaled accordingly.",
        "beat_id": "beat-keywords-bg", "start": 3.30, "end": 8.20,
        "asset": "demo-frames/github-readme-scroll.png",
        "display": "guided-demo",
        "guided_demo": {
            "url": "github.com/coreyhaines31/marketingskills",
            "img_width": 540, "img_height": 9698,
            "pan_moments": [
                {"at": 0,    "x": 50, "y": 24.7},
                {"at": 0.37, "x": 50, "y": 27.7},
                {"at": 0.90, "x": 50, "y": 27.7},
                {"at": 1.12, "x": 50, "y": 29.9},
                {"at": 2.57, "x": 50, "y": 29.9},
                {"at": 4.90, "x": 50, "y": 37.9}
            ],
            "highlight_moments": [
                {"_comment": "content-strategy row", "at": 0,    "duration": 0.85, "region": {"x": 2, "y": 29.71, "w": 96, "h": 0.4}},
                {"_comment": "copywriting row",      "at": 1.12, "duration": 0.85, "region": {"x": 2, "y": 31.71, "w": 96, "h": 0.4}}
            ]
        }
    },
    {
        "_comment": "beat-03a: Head to the repo",
        "beat_id": "beat-03a", "start": 8.20, "end": 10.55,
        "asset": "demo-frames/frame_001.jpg", "display": "guided-demo",
        "guided_demo": {"url": "github.com/coreyhaines31/marketingskills", "img_width": 2560, "img_height": 1340, "pan_moments": [{"at": 0, "x": 5, "y": 0}]}
    },
    {
        "_comment": "beat-03b: Find the skill you want",
        "beat_id": "beat-03b", "start": 10.55, "end": 12.00,
        "asset": "demo-frames/frame_003.jpg", "display": "guided-demo",
        "guided_demo": {"url": "github.com/coreyhaines31/marketingskills", "img_width": 2560, "img_height": 1340, "pan_moments": [{"at": 0, "x": 5, "y": 0}]}
    },
    {
        "_comment": "beat-03c: Click on it",
        "beat_id": "beat-03c", "start": 12.00, "end": 13.80,
        "asset": "demo-frames/frame_007.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "github.com/coreyhaines31/marketingskills", "img_width": 2560, "img_height": 1340,
            "pan_moments": [{"at": 0, "x": 5, "y": 0}],
            "highlight_moments": [{"at": 0.2, "duration": 0.9, "region": {"x": 5, "y": 42, "w": 18, "h": 5}}]
        }
    },
    {
        "_comment": "beat-03d: Code dropdown. Clip 1.26s (was 3.66s). Highlight rescaled: at 0.35, dur 0.80.",
        "beat_id": "beat-03d", "start": 13.80, "end": 15.06,
        "asset": "demo-frames/frame_008.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "github.com/coreyhaines31/marketingskills", "img_width": 2560, "img_height": 1340,
            "pan_moments": [{"at": 0, "x": 48, "y": 0}],
            "highlight_moments": [{"_comment": "Download ZIP button", "at": 0.35, "duration": 0.80, "region": {"x": 42, "y": 48.5, "w": 14, "h": 4}}]
        }
    },
    {
        "_comment": "beat-04a+04b: Claude Customize -> Skills page",
        "beat_id": "beat-04a-b", "start": 15.06, "end": 16.90,
        "asset": "demo-frames/frame_012.jpg", "display": "guided-demo",
        "guided_demo": {"url": "claude.ai/customize/skills", "img_width": 2560, "img_height": 1354, "pan_moments": [{"at": 0, "x": 5, "y": 0}]}
    },
    {
        "_comment": "beat-04c: Click Add",
        "beat_id": "beat-04c", "start": 16.90, "end": 18.00,
        "asset": "demo-frames/frame_013.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "claude.ai/customize/skills", "img_width": 2560, "img_height": 1354,
            "pan_moments": [{"at": 0, "x": 5, "y": 0}],
            "highlight_moments": [{"_comment": "Create skill button", "at": 0.2, "duration": 0.9, "region": {"x": 24, "y": 8, "w": 6, "h": 3}}]
        }
    },
    {
        "_comment": "beat-04d-i: Drag and drop video. Clip 1.85s. playbackRate:2 shows 3.7s of 4s source.",
        "beat_id": "beat-04d-i", "start": 18.00, "end": 19.85,
        "asset": "demo-frames/demo-skill-drop.mp4", "playbackRate": 2
    },
    {
        "_comment": "beat-04d-ii: Done — skills installed. Clip 0.80s (was 0.96s). Highlights rescaled.",
        "beat_id": "beat-04d-ii", "start": 19.85, "end": 20.65,
        "asset": "demo-frames/frame_016.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "claude.ai/customize/skills", "img_width": 2560, "img_height": 1354,
            "pan_moments": [{"at": 0, "x": 0, "y": 0}],
            "highlight_moments": [
                {"_comment": "content-strategy row", "at": 0.02, "duration": 0.23, "region": {"x": 16, "y": 13, "w": 9, "h": 3}},
                {"_comment": "humanizer row",         "at": 0.29, "duration": 0.23, "region": {"x": 16, "y": 17, "w": 9, "h": 3}},
                {"_comment": "skill-creator row",     "at": 0.56, "duration": 0.23, "region": {"x": 16, "y": 21, "w": 9, "h": 3}}
            ]
        }
    },
    {
        "_comment": "beat-05: New chat. Clip 1.35s (was 2.82s). Highlight rescaled.",
        "beat_id": "beat-05", "start": 20.65, "end": 22.00,
        "asset": "demo-frames/frame_017.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "claude.ai/new", "img_width": 2480, "img_height": 1240,
            "pan_moments": [{"at": 0, "x": 50, "y": 0}],
            "highlight_moments": [{"_comment": "Chat input box", "at": 0.38, "duration": 0.80, "region": {"x": 37, "y": 27, "w": 26, "h": 7}}]
        }
    },
    {
        "_comment": "beat-06: Prompt typed. Clip 5.50s (was 6.00s). Highlight rescaled.",
        "beat_id": "beat-06", "start": 22.00, "end": 27.50,
        "asset": "demo-frames/frame_018.jpg", "display": "guided-demo",
        "guided_demo": {
            "url": "claude.ai/new", "img_width": 2560, "img_height": 1354,
            "pan_moments": [{"at": 0, "x": 50, "y": 0}],
            "highlight_moments": [{"_comment": "Dim spotlight on prompt", "at": 0.46, "duration": 2.29, "region": {"x": 36, "y": 33, "w": 28, "h": 20}, "highlight_style": "dim"}]
        }
    },
    {
        "_comment": "beat-07: Claude response scroll. Clip 7.95s (was 6.56s). Pan reaches bottom at 7.5s.",
        "beat_id": "beat-07", "start": 27.50, "end": 35.45,
        "asset": "demo-frames/claude-response-scroll.png", "display": "guided-demo",
        "guided_demo": {
            "url": "claude.ai", "img_width": 540, "img_height": 1344,
            "pan_moments": [{"at": 0, "x": 50, "y": 0}, {"at": 7.5, "x": 50, "y": 100}]
        }
    }
]

tl['lanes']['broll'] = []
tl['lanes']['support'] = []
tl['lanes']['music'] = []

tl['lanes']['sfx'] = [
    {"_comment": "Hook entry whoosh",            "beat_id": "hook-whoosh",             "start": 0,     "end": 1.00,  "asset": "sfx-cinematic-whoosh.mp3", "volume": 0.75},
    {"_comment": "content-strategy pop",         "beat_id": "kw-pop-content-strategy", "start": 3.30,  "end": 3.80,  "asset": "sfx-pop.mp3",              "volume": 0.5},
    {                                            "beat_id": "kw-pop-copywriting",      "start": 4.42,  "end": 4.92,  "asset": "sfx-pop.mp3",              "volume": 0.5},
    {                                            "beat_id": "kw-pop-campaign",         "start": 5.08,  "end": 5.58,  "asset": "sfx-pop.mp3",              "volume": 0.5},
    {"_comment": "FREE impact bass",             "beat_id": "free-impact",             "start": 5.93,  "end": 6.43,  "asset": "sfx-impact-bass.mp3",      "volume": 0.7},
    {"_comment": "30 Seconds whoosh",            "beat_id": "setup-whoosh",            "start": 6.71,  "end": 7.21,  "asset": "sfx-fast-whoosh.mp3",      "volume": 0.55},
    {"_comment": "FlashReset click demo starts", "beat_id": "demo-start-click",        "start": 8.20,  "end": 8.70,  "asset": "sfx-soft-click.mp3",       "volume": 0.45},
    {"_comment": "Cut: repo -> skills list",     "beat_id": "cut-to-skills",           "start": 10.55, "end": 10.95, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Cut: list -> skills folder",   "beat_id": "cut-click-skills",        "start": 12.00, "end": 12.40, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Cut: folder -> code dropdown", "beat_id": "cut-dropdown",            "start": 13.80, "end": 14.20, "asset": "sfx-ui-click.mp3",          "volume": 0.35},
    {"_comment": "Download click",               "beat_id": "download-click",          "start": 14.48, "end": 14.88, "asset": "sfx-ui-click.mp3",          "volume": 0.45},
    {"_comment": "Cut: GitHub -> Claude",        "beat_id": "cut-settings",            "start": 15.06, "end": 15.46, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Cut: settings -> Add button",  "beat_id": "cut-add",                 "start": 16.90, "end": 17.30, "asset": "sfx-ui-click.mp3",          "volume": 0.38},
    {"_comment": "Cut: Add -> upload modal",     "beat_id": "cut-upload-modal",        "start": 18.00, "end": 18.40, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Upload chime skill added",     "beat_id": "upload-chime",            "start": 19.85, "end": 20.35, "asset": "sfx-notification.mp3",      "volume": 0.55},
    {"_comment": "Cut: skills -> new chat",      "beat_id": "cut-new-chat",            "start": 20.65, "end": 21.05, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Cut: new chat -> prompt",      "beat_id": "cut-prompt",              "start": 22.00, "end": 22.40, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "Cut: prompt -> response",      "beat_id": "cut-response",            "start": 27.50, "end": 27.90, "asset": "sfx-ui-click.mp3",          "volume": 0.32},
    {"_comment": "FlashReset whoosh demo ends",  "beat_id": "flash-return-whoosh",     "start": 35.35, "end": 36.05, "asset": "sfx-cinematic-whoosh.mp3",  "volume": 0.7},
    {"_comment": "CTA entry whoosh",             "beat_id": "cta-whoosh",              "start": 38.90, "end": 39.40, "asset": "sfx-fast-whoosh.mp3",       "volume": 0.55}
]

tl['lanes']['overlays'] = [
    {
        "_comment": "Claude logo bounce+trail during hook",
        "beat_id": "logo-hook", "type": "LogoOverlay", "start": 0, "end": 3.30,
        "props": {"src": "brands/Claude-orange.svg", "size": 80, "position": "top-right", "bounce": True, "bounceFrequency": 1.5, "bounceAmplitude": 22, "trail": True, "trailLayers": 3, "trailLagInFrames": 4}
    },
    {"_comment": "CONTENT STRATEGY", "beat_id": "kw-content-strategy",  "type": "OverlayKeyword", "start": 3.30, "end": 4.24, "props": {"text": "CONTENT STRATEGY",  "color": "#D97757", "fontSize": 72, "fontWeight": 900, "position": "center", "autoSize": True}},
    {                                "beat_id": "kw-copywriting",        "type": "OverlayKeyword", "start": 4.42, "end": 4.94, "props": {"text": "COPYWRITING",        "color": "#D97757", "fontSize": 64, "fontWeight": 900, "position": "center"}},
    {                                "beat_id": "kw-campaign-planning",  "type": "OverlayKeyword", "start": 5.08, "end": 5.88, "props": {"text": "CAMPAIGN PLANNING",  "color": "#D97757", "fontSize": 72, "fontWeight": 900, "position": "center", "autoSize": True}},
    {"_comment": "FREE",             "beat_id": "kw-free",               "type": "OverlayKeyword", "start": 5.93, "end": 6.33, "props": {"text": "FREE",               "color": "#D97757", "fontSize": 96, "fontWeight": 900, "position": "center"}},
    {"_comment": "30 SECONDS",       "beat_id": "kw-30-seconds",         "type": "OverlayKeyword", "start": 6.71, "end": 8.10, "props": {"text": "30 SECONDS",         "color": "#FAF9F5", "fontSize": 72, "fontWeight": 900, "position": "center"}},
    {"_comment": "FlashReset into demo",  "beat_id": "flash-into-demo",  "type": "FlashReset", "start": 8.20,  "end": 8.30,  "props": {}},
    {"_comment": "FlashReset demo end",   "beat_id": "flash-demo-end",   "type": "FlashReset", "start": 35.35, "end": 35.45, "props": {}},
    {"_comment": "THOUSANDS cost",        "beat_id": "kw-thousands",      "type": "OverlayKeyword", "start": 35.45, "end": 38.25, "props": {"text": "THOUSANDS", "color": "#D97757", "fontSize": 96, "fontWeight": 900, "position": "center"}},
    {"_comment": "SKILLS CTA",            "beat_id": "kw-skills-cta",     "type": "OverlayKeyword", "start": 38.90, "end": 42.07, "props": {"text": "SKILLS",    "color": "#D97757", "fontSize": 96, "fontWeight": 900, "position": "center"}}
]

tl['lanes']['captions'] = [
    {"beat_id": "cap-01a", "start": 0,     "end": 1.63,  "text": "Someone just dropped"},
    {"beat_id": "cap-01b", "start": 1.63,  "end": 3.30,  "text": "29 Claude Marketing Skills"},
    {"beat_id": "cap-02a", "start": 3.30,  "end": 3.99,  "text": "Content Strategy"},
    {"beat_id": "cap-02b", "start": 4.42,  "end": 4.80,  "text": "Copywriting"},
    {"beat_id": "cap-02c", "start": 5.08,  "end": 5.67,  "text": "Campaign Planning"},
    {"beat_id": "cap-02d", "start": 5.93,  "end": 6.23,  "text": "All Free"},
    {"beat_id": "cap-03",  "start": 6.71,  "end": 8.10,  "text": "Setup Takes 30 Seconds"},
    {"beat_id": "cap-04a", "start": 8.20,  "end": 8.94,  "text": "Head to the repo"},
    {"beat_id": "cap-04b", "start": 9.45,  "end": 10.40, "text": "Find the skill you want"},
    {"beat_id": "cap-04c", "start": 10.76, "end": 11.34, "text": "Click on it"},
    {"beat_id": "cap-04d", "start": 11.78, "end": 12.75, "text": "Hit SKILL.md"},
    {"beat_id": "cap-04e", "start": 13.65, "end": 14.57, "text": "Download the skill file"},
    {"beat_id": "cap-05a", "start": 15.08, "end": 16.20, "text": "Go to Claude"},
    {"beat_id": "cap-05b", "start": 16.70, "end": 17.26, "text": "Customize"},
    {"beat_id": "cap-05c", "start": 17.86, "end": 18.17, "text": "Skills"},
    {"beat_id": "cap-05d", "start": 18.75, "end": 19.27, "text": "Click Add"},
    {"beat_id": "cap-05e", "start": 19.78, "end": 20.90, "text": "Drag and drop it in"},
    {"beat_id": "cap-05f", "start": 21.39, "end": 21.57, "text": "Done."},
    {"beat_id": "cap-06",  "start": 21.57, "end": 23.44, "text": "Now open a new chat"},
    {"beat_id": "cap-07a", "start": 24.11, "end": 26.21, "text": "Tell Claude to build a content strategy"},
    {"beat_id": "cap-07b", "start": 26.21, "end": 28.97, "text": "for my consulting YouTube channel"},
    {"beat_id": "cap-08a", "start": 29.53, "end": 30.54, "text": "It pulls the skill"},
    {"beat_id": "cap-08b", "start": 31.10, "end": 32.29, "text": "runs the full framework"},
    {"beat_id": "cap-08c", "start": 32.89, "end": 35.45, "text": "delivers everything in clearly laid out steps"},
    {"beat_id": "cap-09",  "start": 35.45, "end": 38.35, "text": "Instead of paying an agency thousands"},
    {"beat_id": "cap-10a", "start": 38.91, "end": 40.15, "text": "Comment SKILLS"},
    {"beat_id": "cap-10b", "start": 40.15, "end": 42.07, "text": "and I'll DM you the link"}
]

with open(r'D:\Reel generation\remotion\public\timeline.json', 'w', encoding='utf-8') as f:
    json.dump(tl, f, indent=2, ensure_ascii=False)

print("Done. timeline.json remapped to 42.07s.")
print(f"  avatar entries: {len(tl['lanes']['avatar'])}")
print(f"  demo entries:   {len(tl['lanes']['demo'])}")
print(f"  sfx entries:    {len(tl['lanes']['sfx'])}")
print(f"  overlay entries:{len(tl['lanes']['overlays'])}")
print(f"  caption entries:{len(tl['lanes']['captions'])}")
