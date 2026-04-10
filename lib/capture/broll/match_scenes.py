"""
Step 3: Match classified b-roll scenes to script beats.

Uses embedding similarity (cosine) to find the best b-roll scene for each
beat in the beat map that needs visual support. Outputs a match plan that
can be reviewed before cutting.

Usage:
    python -m lib.capture.broll.match_scenes <broll_dir> <project_dir> [--top-k 3]

Input:
    <broll_dir>/scene_list.json  (classified, with embeddings)
    <project_dir>/audio/beat-map.json
    <project_dir>/script.md (optional — for richer beat context)

Output:
    <project_dir>/output/broll_matches.json
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

from google import genai


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_beat_text(beat: dict) -> str:
    """Extract searchable text from a beat map entry."""
    parts = []
    if beat.get("text"):
        parts.append(beat["text"])
    if beat.get("intent"):
        parts.append(f"intent: {beat['intent']}")
    if beat.get("visual_plan"):
        parts.append(f"visual: {beat['visual_plan']}")
    if beat.get("notes"):
        parts.append(beat["notes"])
    return " ".join(parts) if parts else f"beat {beat.get('beat_id', 'unknown')}"


def match_scenes(broll_dir: str, project_dir: str, top_k: int = 3,
                 api_key: str | None = None) -> list[dict]:
    """Match b-roll scenes to script beats using embedding similarity.

    Args:
        broll_dir: Directory with classified scene_list.json
        project_dir: Project directory with beat-map.json
        top_k: Number of candidate matches per beat
        api_key: Gemini API key for embedding beat text

    Returns:
        List of match results
    """
    broll_dir = Path(broll_dir)
    project_dir = Path(project_dir)

    # ── Load scene data ──
    scene_meta_path = broll_dir / "scene_list.json"
    if not scene_meta_path.exists():
        print(f"Error: scene_list.json not found in {broll_dir}")
        sys.exit(1)

    with open(scene_meta_path) as f:
        scene_data = json.load(f)

    scenes = scene_data["scenes"]
    scenes_with_embeddings = [s for s in scenes if s.get("embedding")]

    if not scenes_with_embeddings:
        print("Error: No scenes have embeddings. Run classify_scenes first.")
        sys.exit(1)

    # ── Load beat map ──
    beat_map_path = project_dir / "audio" / "beat-map.json"
    if not beat_map_path.exists():
        print(f"Error: beat-map.json not found at {beat_map_path}")
        sys.exit(1)

    with open(beat_map_path) as f:
        beat_map = json.load(f)

    beats = beat_map if isinstance(beat_map, list) else beat_map.get("beats", [])

    # ── Load existing timeline to know which beats already have visuals ──
    timeline_path = project_dir / "output" / "timeline.json"
    existing_visual_beats = set()
    if timeline_path.exists():
        with open(timeline_path) as f:
            timeline = json.load(f)
        for lane in ["demo", "support", "broll"]:
            for entry in timeline.get("lanes", {}).get(lane, []):
                if entry.get("beat_id"):
                    existing_visual_beats.add(entry["beat_id"])

    # ── Identify beats that need b-roll ──
    # Beats with intent "demo", "proof", "context", "transition" are candidates
    # Skip beats that already have visuals assigned
    broll_intents = {"demo", "proof", "context", "transition", "setup", "news-hit"}
    candidate_beats = []
    for beat in beats:
        beat_id = beat.get("beat_id", "")
        intent = beat.get("intent", "").lower()
        if beat_id in existing_visual_beats:
            continue  # already has a visual
        if intent in broll_intents or not intent:
            candidate_beats.append(beat)

    if not candidate_beats:
        print("No beats need b-roll — all have visuals or are avatar-only.")
        # Still output empty matches file
        output_path = project_dir / "output" / "broll_matches.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({"matches": [], "note": "All beats already have visuals"}, f, indent=2)
        return []

    print(f"Found {len(candidate_beats)} beats needing b-roll from {len(scenes_with_embeddings)} classified scenes.")

    # ── Generate embeddings for beat text ──
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY not set.")
        sys.exit(1)

    client = genai.Client(api_key=key)
    embed_model = "gemini-embedding-001"

    matches = []
    used_scenes = set()  # track used scenes to avoid duplicates

    for beat in candidate_beats:
        beat_text = get_beat_text(beat)
        beat_id = beat.get("beat_id", "unknown")

        print(f"  Matching {beat_id}: \"{beat_text[:60]}...\"")

        try:
            # Embed the beat text as a query
            result = client.models.embed_content(
                model=embed_model,
                contents=beat_text,
            )
            beat_embedding = result.embeddings[0].values
        except Exception as e:
            print(f"    Embedding failed: {e}")
            continue

        # ── Rank scenes by cosine similarity ──
        scored = []
        for scene in scenes_with_embeddings:
            if scene["id"] in used_scenes:
                continue  # don't reuse scenes
            sim = cosine_similarity(beat_embedding, scene["embedding"])
            scored.append((sim, scene))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored[:top_k]

        if top_matches:
            best_sim, best_scene = top_matches[0]
            match_entry = {
                "beat_id": beat_id,
                "beat_text": beat_text,
                "beat_start": beat.get("start"),
                "beat_end": beat.get("end"),
                "best_match": {
                    "scene_id": best_scene["id"],
                    "file": best_scene["file"],
                    "description": best_scene.get("description", ""),
                    "labels": best_scene.get("labels", []),
                    "similarity": round(best_sim, 4),
                    "duration": best_scene.get("duration", 0),
                },
                "candidates": [
                    {
                        "scene_id": s["id"],
                        "description": s.get("description", ""),
                        "similarity": round(sim, 4),
                        "duration": s.get("duration", 0),
                    }
                    for sim, s in top_matches
                ],
                "approved": False,  # Claude Code reviews and sets to True
            }
            matches.append(match_entry)

            # Reserve best match to avoid reuse
            used_scenes.add(best_scene["id"])

    # ── Write match plan ──
    output_path = project_dir / "output" / "broll_matches.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "source_video": scene_data.get("source", ""),
        "total_scenes": len(scenes),
        "beats_matched": len(matches),
        "matches": matches,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. {len(matches)} matches written to {output_path}")
    print("Review broll_matches.json, set 'approved': true for each, then run cut_scenes.")
    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Match b-roll scenes to script beats")
    parser.add_argument("broll_dir", help="Directory with classified scene_list.json")
    parser.add_argument("project_dir", help="Project directory with audio/beat-map.json")
    parser.add_argument("--top-k", type=int, default=3, help="Candidates per beat (default 3)")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    args = parser.parse_args()
    match_scenes(args.broll_dir, args.project_dir, args.top_k, args.api_key)
