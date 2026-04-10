"""
Step 2: Classify each scene using Gemini.

Sends each scene's thumbnail to Gemini for visual description and labeling,
then generates an embedding for semantic matching against script beats.

Usage:
    python -m lib.capture.broll.classify_scenes <broll_dir> [--api-key KEY]

Requires:
    GEMINI_API_KEY environment variable or --api-key flag

Input:
    <broll_dir>/scene_list.json (from split_scenes)
    <broll_dir>/thumbnails/*.jpg

Output:
    Updates scene_list.json with labels and embeddings per scene
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

from google import genai


# ── Label taxonomy for b-roll classification ──
LABEL_TAXONOMY = [
    # Visual content
    "technology", "software-ui", "coding", "ai-interface", "chatbot",
    "mobile-app", "website", "dashboard", "data-visualization",
    # People & action
    "person-talking", "person-typing", "hands-device", "collaboration",
    "presentation", "interview", "crowd", "audience",
    # Environment
    "office", "workspace", "studio", "outdoor", "cityscape", "nature",
    "abstract", "aerial",
    # Objects
    "laptop", "phone", "tablet", "camera", "microphone", "screen",
    # Mood/style
    "cinematic", "fast-paced", "slow-motion", "close-up", "wide-shot",
    "transition", "title-card", "text-overlay", "logo",
    # Language/education specific
    "language-learning", "vocabulary", "translation", "conversation",
    "reading", "writing", "cultural", "travel", "food",
]

CLASSIFY_PROMPT = """Analyze this video frame thumbnail and provide:

1. **description**: A concise 1-2 sentence description of what's shown
2. **labels**: Pick 3-6 labels from this taxonomy that best describe the content:
   {taxonomy}
3. **mood**: One word for the visual mood (e.g., energetic, calm, professional, playful, dramatic)
4. **motion**: Estimated motion level: "static", "slow", "moderate", "fast"
5. **suitable_for**: What type of reel beat this would work for (e.g., "hook", "demo", "transition", "cta", "proof", "b-roll-filler")

Return valid JSON only, no markdown fencing:
{{"description": "...", "labels": ["...", "..."], "mood": "...", "motion": "...", "suitable_for": "..."}}"""


MAX_RETRIES = 3
RETRY_BASE_DELAY = 30  # seconds


def encode_image(path: Path) -> str:
    """Read image file and return base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_with_retry(fn, retries=MAX_RETRIES):
    """Call a function with exponential backoff on 429 errors."""
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                wait = RETRY_BASE_DELAY * (attempt + 1)
                print(f"    Rate limited — waiting {wait}s (attempt {attempt+1}/{retries})...")
                time.sleep(wait)
            else:
                raise


def classify_scenes(broll_dir: str, api_key: str | None = None) -> list[dict]:
    """Classify all scenes in a b-roll directory using Gemini."""
    broll_dir = Path(broll_dir)
    meta_path = broll_dir / "scene_list.json"

    if not meta_path.exists():
        print(f"Error: scene_list.json not found in {broll_dir}")
        print("Run split_scenes first.")
        sys.exit(1)

    with open(meta_path) as f:
        data = json.load(f)

    scenes = data["scenes"]

    # ── Configure Gemini ──
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY not set. Pass --api-key or set the env var.")
        sys.exit(1)

    client = genai.Client(api_key=key)

    # Models
    vision_model = "gemini-2.0-flash"
    embed_model = "gemini-embedding-001"

    # Skip already-classified scenes (resume support)
    remaining = [s for s in scenes if not s.get("labels") or s["labels"] == []]
    if len(remaining) < len(scenes):
        print(f"Resuming — {len(scenes) - len(remaining)} already classified, {len(remaining)} remaining.")

    print(f"Classifying {len(remaining)} scenes with Gemini...")

    for i, scene in enumerate(remaining):
        thumb_path = broll_dir / scene["thumbnail"]
        if not thumb_path.exists():
            print(f"  Warning: thumbnail missing for {scene['id']}, skipping")
            continue

        print(f"  Classifying {scene['id']} ({i+1}/{len(remaining)})...")

        # ── Vision classification with retry ──
        try:
            img_data = encode_image(thumb_path)
            prompt = CLASSIFY_PROMPT.format(taxonomy=", ".join(LABEL_TAXONOMY))

            def do_classify():
                return client.models.generate_content(
                    model=vision_model,
                    contents=[
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_data}},
                        prompt,
                    ],
                )

            response = call_with_retry(do_classify)

            # Parse response
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            classification = json.loads(text)
            scene["labels"] = classification.get("labels", [])
            scene["description"] = classification.get("description", "")
            scene["mood"] = classification.get("mood", "")
            scene["motion"] = classification.get("motion", "")
            scene["suitable_for"] = classification.get("suitable_for", "")

        except Exception as e:
            print(f"    Vision classification failed: {e}")
            scene["labels"] = []
            scene["description"] = f"Classification failed: {e}"

        # ── Generate text embedding with retry ──
        if scene.get("labels"):
            try:
                embed_text = f"{scene.get('description', '')} {' '.join(scene.get('labels', []))}"

                def do_embed():
                    return client.models.embed_content(
                        model=embed_model,
                        contents=embed_text,
                    )

                embed_result = call_with_retry(do_embed)
                scene["embedding"] = list(embed_result.embeddings[0].values)

            except Exception as e:
                print(f"    Embedding failed: {e}")
                scene["embedding"] = None

        # Rate limit — space requests 4s apart for free tier (15 RPM)
        time.sleep(4.0)

        # Save progress every 5 scenes (crash recovery)
        if (i + 1) % 5 == 0:
            data["scenes"] = scenes
            with open(meta_path, "w") as f:
                json.dump(data, f, indent=2)

    # ── Final save ──
    data["scenes"] = scenes
    data["classified"] = True
    with open(meta_path, "w") as f:
        json.dump(data, f, indent=2)

    classified_count = sum(1 for s in scenes if s.get("labels") and s["labels"] != [])
    print(f"\nDone. {classified_count}/{len(scenes)} scenes classified.")
    print(f"Updated: {meta_path}")
    return scenes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify b-roll scenes with Gemini")
    parser.add_argument("broll_dir", help="Directory with scene_list.json from split_scenes")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    args = parser.parse_args()
    classify_scenes(args.broll_dir, args.api_key)
