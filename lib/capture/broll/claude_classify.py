"""
Inject Claude's visual classifications into scene_list.json,
then run Gemini Embedding only (no Flash vision needed).

Usage:
    python -m lib.capture.broll.claude_classify <broll_dir> [--embed --api-key KEY]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from google import genai


# ── Claude's classifications for each scene (from visual inspection) ──
CLASSIFICATIONS = {
    "scene_001": {
        "description": "Stack of colorful books in a stone/marble setting, warm tones, vintage illustration style",
        "labels": ["language-learning", "cultural", "close-up", "cinematic"],
        "mood": "warm",
        "motion": "slow",
        "suitable_for": "hook"
    },
    "scene_002": {
        "description": "Glowing Google 'G' logo with neon lab/science aesthetic, dark background with vibrant colors",
        "labels": ["logo", "technology", "ai-interface", "cinematic"],
        "mood": "dramatic",
        "motion": "slow",
        "suitable_for": "hook"
    },
    "scene_003": {
        "description": "Hand holding phone showing 'Language Help' text on gradient screen, colorful UI elements",
        "labels": ["phone", "mobile-app", "language-learning", "hands-device"],
        "mood": "playful",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_004": {
        "description": "Single worn blue and gold book on wooden surface, vintage aesthetic, warm lighting",
        "labels": ["language-learning", "close-up", "cinematic"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "b-roll-filler"
    },
    "scene_005": {
        "description": "Phone with chat bubbles on colorful desk with lamp and pencil, illustrated style",
        "labels": ["phone", "chatbot", "language-learning", "workspace"],
        "mood": "playful",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_006": {
        "description": "Desk with lamp illuminating blank paper, retro illustration style, warm amber tones",
        "labels": ["workspace", "writing", "close-up", "cinematic"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "b-roll-filler"
    },
    "scene_007": {
        "description": "Phone with WiFi symbol on a notebook, simple clean composition",
        "labels": ["phone", "technology", "close-up"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "transition"
    },
    "scene_008": {
        "description": "Phone with WiFi and Google logo on notebook paper, colorful illustrated style",
        "labels": ["phone", "logo", "technology", "language-learning"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_009": {
        "description": "Phone with Google logo and globe/location pin on grid paper, travel concept",
        "labels": ["phone", "logo", "travel", "language-learning"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_010": {
        "description": "Traveler with backpack reading map in neon-lit Japanese street, vibrant night scene",
        "labels": ["travel", "cultural", "cinematic", "wide-shot"],
        "mood": "energetic",
        "motion": "moderate",
        "suitable_for": "hook"
    },
    "scene_011": {
        "description": "Airplane with emergency light, chat bubble, and treasure chest icons, conceptual illustration",
        "labels": ["travel", "language-learning", "abstract", "cinematic"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "transition"
    },
    "scene_012": {
        "description": "Close-up of hand holding phone showing app icons, warm tones",
        "labels": ["phone", "hands-device", "mobile-app", "close-up"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_013": {
        "description": "Close-up of a search/text input field UI element, minimal",
        "labels": ["software-ui", "close-up", "technology"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "demo"
    },
    "scene_014": {
        "description": "Phone with gradient pink/purple screen, clean minimal composition",
        "labels": ["phone", "mobile-app", "close-up"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "transition"
    },
    "scene_015": {
        "description": "Glowing science flask/beaker with radiating light beams on dark background",
        "labels": ["abstract", "technology", "cinematic", "close-up"],
        "mood": "dramatic",
        "motion": "slow",
        "suitable_for": "transition"
    },
    "scene_016": {
        "description": "Phone showing app properties/settings with 'BETA VERSION' badge, language options visible",
        "labels": ["phone", "software-ui", "mobile-app", "language-learning"],
        "mood": "professional",
        "motion": "static",
        "suitable_for": "demo"
    },
    "scene_017": {
        "description": "Stressed traveler at airport struggling with overstuffed backpack, items flying everywhere",
        "labels": ["travel", "person-talking", "cinematic", "fast-paced"],
        "mood": "energetic",
        "motion": "fast",
        "suitable_for": "hook"
    },
    "scene_018": {
        "description": "Hand holding phone showing 'Tiny Lesson' app with 'Common Travel Phrases' section, colorful UI",
        "labels": ["phone", "mobile-app", "language-learning", "hands-device", "vocabulary"],
        "mood": "playful",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_019": {
        "description": "Close-up of finger pressing send button on phone with warning icon, text input visible",
        "labels": ["phone", "hands-device", "close-up", "software-ui"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_020": {
        "description": "Phone showing 'I lost my passport' with translation phrases: embassy location, missing document report",
        "labels": ["phone", "mobile-app", "language-learning", "translation", "travel"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_021": {
        "description": "Traveler at desk with official/police officer, warning signs, urgent situation illustration",
        "labels": ["travel", "person-talking", "collaboration", "cinematic"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "proof"
    },
    "scene_022": {
        "description": "Red apple with blue and yellow geometric overlay, clean centered composition, object recognition concept",
        "labels": ["close-up", "abstract", "language-learning", "vocabulary"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "demo"
    },
    "scene_023": {
        "description": "Person looking down at phone with serene expression, blue-toned illustration, face lit by screen",
        "labels": ["person-talking", "phone", "close-up", "cinematic"],
        "mood": "calm",
        "motion": "slow",
        "suitable_for": "b-roll-filler"
    },
    "scene_024": {
        "description": "Woman at airport terminal with luggage, warm golden tones, travel scene",
        "labels": ["travel", "person-talking", "cinematic", "wide-shot"],
        "mood": "calm",
        "motion": "slow",
        "suitable_for": "b-roll-filler"
    },
    "scene_025": {
        "description": "Outdoor food market scene at sunset, plate of food in foreground, people dining",
        "labels": ["food", "cultural", "travel", "wide-shot", "cinematic"],
        "mood": "warm",
        "motion": "moderate",
        "suitable_for": "b-roll-filler"
    },
    "scene_026": {
        "description": "Phone on wooden table showing social media video of two people, hearts and engagement icons",
        "labels": ["phone", "mobile-app", "conversation", "cinematic"],
        "mood": "playful",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_027": {
        "description": "Video player showing two people laughing while eating, pause button visible, conversation scene",
        "labels": ["conversation", "food", "cultural", "cinematic"],
        "mood": "warm",
        "motion": "moderate",
        "suitable_for": "proof"
    },
    "scene_028": {
        "description": "Timeline/progress bar with slang words 'Chuffed' and 'Knackered' as vocabulary markers",
        "labels": ["vocabulary", "language-learning", "software-ui", "data-visualization"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_029": {
        "description": "Hand pressing large red 'PAUSE' button on a media player interface, dramatic close-up",
        "labels": ["hands-device", "close-up", "software-ui", "cinematic"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_030": {
        "description": "Two people having animated conversation at table with phone between them, colorful chat bubbles above",
        "labels": ["conversation", "collaboration", "language-learning", "cinematic"],
        "mood": "energetic",
        "motion": "moderate",
        "suitable_for": "proof"
    },
    "scene_031": {
        "description": "Phone showing camera permission dialog 'Allow Camera to take pictures and record video?'",
        "labels": ["phone", "software-ui", "camera", "hands-device"],
        "mood": "professional",
        "motion": "static",
        "suitable_for": "demo"
    },
    "scene_032": {
        "description": "Decorated coffee mug and leather satchel on wooden table, warm cultural cafe scene",
        "labels": ["cultural", "food", "travel", "close-up", "cinematic"],
        "mood": "warm",
        "motion": "static",
        "suitable_for": "b-roll-filler"
    },
    "scene_033": {
        "description": "Phone with gradient teal-to-purple screen, centered clean composition, minimal",
        "labels": ["phone", "mobile-app", "close-up"],
        "mood": "calm",
        "motion": "static",
        "suitable_for": "transition"
    },
    "scene_034": {
        "description": "European street scene with AR-style icons and labels floating above buildings, bicycle in foreground",
        "labels": ["travel", "ai-interface", "cultural", "wide-shot", "cinematic"],
        "mood": "energetic",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_035": {
        "description": "Hand touching glowing 'VOCABULARY' card with geometric shapes, magical learning concept",
        "labels": ["vocabulary", "language-learning", "abstract", "close-up", "cinematic"],
        "mood": "dramatic",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_036": {
        "description": "Three icons on dark background: emergency siren, speech bubble, camera — representing three app features",
        "labels": ["abstract", "technology", "cinematic"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "transition"
    },
    "scene_037": {
        "description": "Three icons: warning/alert siren, speech bubble with audio waves, camera — zoomed/highlighted view",
        "labels": ["abstract", "technology", "cinematic"],
        "mood": "dramatic",
        "motion": "moderate",
        "suitable_for": "transition"
    },
    "scene_038": {
        "description": "Three panel dark composition: red siren, blue glowing chat bubble, gray camera icon",
        "labels": ["abstract", "technology", "cinematic"],
        "mood": "dramatic",
        "motion": "slow",
        "suitable_for": "transition"
    },
    "scene_039": {
        "description": "Three panel composition: realistic red siren, neon blue speech bubble, green glowing camera lens",
        "labels": ["abstract", "technology", "cinematic", "close-up"],
        "mood": "dramatic",
        "motion": "slow",
        "suitable_for": "cta"
    },
    "scene_040": {
        "description": "Phone with glowing green screen surrounded by notes, pencils, warning icons — learning toolkit concept",
        "labels": ["phone", "technology", "language-learning", "cinematic"],
        "mood": "energetic",
        "motion": "moderate",
        "suitable_for": "cta"
    },
    "scene_041": {
        "description": "Two hands holding phone showing messaging/chat app interface, close-up",
        "labels": ["phone", "hands-device", "chatbot", "mobile-app", "close-up"],
        "mood": "professional",
        "motion": "slow",
        "suitable_for": "demo"
    },
    "scene_042": {
        "description": "Close-up of phone screen showing chat interface with keyboard visible, finger typing",
        "labels": ["phone", "hands-device", "chatbot", "software-ui", "close-up"],
        "mood": "professional",
        "motion": "moderate",
        "suitable_for": "demo"
    },
    "scene_043": {
        "description": "Phone showing 'Setup Toolkit' header on clean white screen, minimal UI",
        "labels": ["phone", "software-ui", "mobile-app", "technology"],
        "mood": "professional",
        "motion": "static",
        "suitable_for": "cta"
    },
}


def inject_classifications(broll_dir: str) -> dict:
    """Write Claude's classifications into scene_list.json."""
    broll_dir = Path(broll_dir)
    meta_path = broll_dir / "scene_list.json"

    if not meta_path.exists():
        print(f"Error: scene_list.json not found in {broll_dir}")
        sys.exit(1)

    with open(meta_path) as f:
        data = json.load(f)

    updated = 0
    for scene in data["scenes"]:
        sid = scene["id"]
        if sid in CLASSIFICATIONS:
            c = CLASSIFICATIONS[sid]
            scene["description"] = c["description"]
            scene["labels"] = c["labels"]
            scene["mood"] = c["mood"]
            scene["motion"] = c["motion"]
            scene["suitable_for"] = c["suitable_for"]
            updated += 1

    data["classified"] = True
    with open(meta_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Injected {updated} classifications into {meta_path}")
    return data


def run_embeddings(broll_dir: str, api_key: str | None = None):
    """Generate Gemini embeddings for all classified scenes (no Flash vision needed)."""
    broll_dir = Path(broll_dir)
    meta_path = broll_dir / "scene_list.json"

    with open(meta_path) as f:
        data = json.load(f)

    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY not set.")
        sys.exit(1)

    client = genai.Client(api_key=key)
    embed_model = "gemini-embedding-001"

    scenes = data["scenes"]
    need_embedding = [s for s in scenes if s.get("labels") and not s.get("embedding")]

    if not need_embedding:
        print("All classified scenes already have embeddings.")
        return

    print(f"Generating embeddings for {len(need_embedding)} scenes...")

    for i, scene in enumerate(need_embedding):
        embed_text = f"{scene.get('description', '')} {' '.join(scene.get('labels', []))}"
        print(f"  Embedding {scene['id']} ({i+1}/{len(need_embedding)})...")

        try:
            result = client.models.embed_content(
                model=embed_model,
                contents=embed_text,
            )
            scene["embedding"] = list(result.embeddings[0].values)
        except Exception as e:
            if "429" in str(e):
                print(f"    Rate limited — waiting 30s...")
                time.sleep(30)
                try:
                    result = client.models.embed_content(
                        model=embed_model,
                        contents=embed_text,
                    )
                    scene["embedding"] = list(result.embeddings[0].values)
                except Exception as e2:
                    print(f"    Embedding failed after retry: {e2}")
                    scene["embedding"] = None
            else:
                print(f"    Embedding failed: {e}")
                scene["embedding"] = None

        # Rate limit spacing — 4s for free tier
        time.sleep(4)

        # Save progress every 5
        if (i + 1) % 5 == 0:
            with open(meta_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"    Progress saved ({i+1}/{len(need_embedding)})")

    # Final save
    with open(meta_path, "w") as f:
        json.dump(data, f, indent=2)

    embedded = sum(1 for s in scenes if s.get("embedding"))
    print(f"\nDone. {embedded}/{len(scenes)} scenes have embeddings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject Claude classifications + Gemini embeddings")
    parser.add_argument("broll_dir", help="Directory with scene_list.json")
    parser.add_argument("--embed", action="store_true", help="Also run Gemini embeddings after injecting")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    args = parser.parse_args()

    inject_classifications(args.broll_dir)

    if args.embed:
        run_embeddings(args.broll_dir, args.api_key)
