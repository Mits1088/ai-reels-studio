"""
Derive Style Pack

Reads training-example.json files and produces machine-readable derived artifacts
that the rest of the pipeline consumes. This is the single translation layer between
training data and repo rules/skills/assembly.

Usage:
    python training/derive_style_pack.py
    python training/derive_style_pack.py --example training/references/nicholas-processed/training-example.json

Outputs (to training/derived/):
    template-registry.json   — template definitions with avatar/split/caption/bg behavior
    rhythm-bounds.json       — min/max thresholds for QA validation
    caption-modes.json       — headline mode spec, suppression rules, emphasis rules
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

TRAINING_DIR = Path(__file__).parent
DERIVED_DIR = TRAINING_DIR / "derived"
INDEX_PATH = TRAINING_DIR / "training-index.json"


def load_examples(specific_path=None):
    """Load training examples from index or specific path."""
    if specific_path:
        with open(specific_path) as f:
            return [json.load(f)]

    with open(INDEX_PATH) as f:
        index = json.load(f)

    examples = []
    for entry in index["examples"]:
        if entry["status"] != "complete":
            continue
        path = TRAINING_DIR / entry["file"]
        if path.exists():
            with open(path, encoding="utf-8") as f:
                examples.append(json.load(f))
    return examples


def derive_template_registry(examples):
    """
    Extract template definitions from all training examples.
    Each template gets: id, description, avatar mode, split ratio,
    background type, caption behavior, proof classes it serves.
    """
    templates = {}

    for ex in examples:
        style_card = ex.get("style_card", {})
        segments = ex["completion"]["segments"]

        for seg in segments:
            tid = seg["template"]
            if tid.startswith("TODO"):
                continue

            if tid not in templates:
                templates[tid] = {
                    "id": tid,
                    "description": "",
                    "avatar_mode": "",
                    "split_ratio": None,
                    "background": "",
                    "caption_behavior": "standard",
                    "proof_classes_served": [],
                    "seen_in": [],
                    "occurrences": 0,
                }

            t = templates[tid]
            t["occurrences"] += 1

            # Track which examples use this template
            creator = ex["meta"]["creator"]
            if creator not in t["seen_in"]:
                t["seen_in"].append(creator)

            # Track proof classes
            pc = seg.get("proof_class")
            if pc and pc not in t["proof_classes_served"]:
                t["proof_classes_served"].append(pc)

    # Now enrich with avatar/split/caption from the segment data
    for ex in examples:
        for seg in ex["completion"]["segments"]:
            tid = seg["template"]
            if tid not in templates:
                continue
            t = templates[tid]

            # Avatar mode — take the most specific one seen
            avatar = seg.get("avatar", "")
            if avatar and (not t["avatar_mode"] or len(avatar) > len(t["avatar_mode"])):
                t["avatar_mode"] = avatar

            # Caption behavior — derive from suppression
            if seg.get("caption_suppression_reason"):
                t["caption_behavior"] = "suppressed"
            elif seg.get("caption") and "section-label" in str(seg.get("caption", "")):
                t["caption_behavior"] = "section-label"
            elif "badge-overlay" in str(seg.get("caption_data", seg.get("caption", ""))):
                t["caption_behavior"] = "badge-overlay"

    # Derive split ratios and backgrounds from template semantics
    split_map = {
        "logo-reveal-split": {"ratio": "50/50", "bg": "warm-beige"},
        "proof-overlay-split": {"ratio": "65/35", "bg": "content-driven"},
        "card-carousel": {"ratio": "100/0", "bg": "dark"},
        "demo-fullscreen": {"ratio": "100/0", "bg": "content-driven"},
        "avatar-overlay": {"ratio": "0/100", "bg": "natural"},
        "proof-fullscreen-warm": {"ratio": "100/0", "bg": "warm-beige"},
        "proof-fullscreen-dark": {"ratio": "100/0", "bg": "dark"},
        "text-fullscreen-dark": {"ratio": "100/0", "bg": "dark"},
        "avatar-direct": {"ratio": "0/100", "bg": "natural"},
        "split-screen-standard": {"ratio": "40/60", "bg": "aurora-white"},
        "montage-rapid": {"ratio": "100/0", "bg": "content-driven"},
        "hero-text-card": {"ratio": "100/0", "bg": "theme-primary"},
    }

    desc_map = {
        "logo-reveal-split": "Logo animation top half + presenter bottom half. Hook only.",
        "proof-overlay-split": "Proof screenshot dominates top 60-65%, presenter head peeks from bottom 35%. Proof-heavy split.",
        "card-carousel": "Rapid dark cards cycling one at a time, centered, no avatar. For breadth proof.",
        "demo-fullscreen": "Full-screen UI recording with cursor, no avatar, no caption. UI is the narrative.",
        "avatar-overlay": "Presenter full-screen with floating overlays ON body (icons, badges, checklists, cards).",
        "proof-fullscreen-warm": "Output proof screenshot on warm beige background, no avatar. Shows real deliverables.",
        "proof-fullscreen-dark": "Output proof on dark background, no avatar.",
        "text-fullscreen-dark": "Document text on dark background, scrolling, no avatar.",
        "avatar-direct": "Clean presenter full-screen, no overlays, caption only. For direct address and closing.",
        "split-screen-standard": "Standard 40/60 split — content top 40%, avatar bottom 60%. Default for cinematic-presenter.",
        "montage-rapid": "Multiple images rapid-cut, 0.5-1s each, no avatar. For recap or breadth sequences.",
        "hero-text-card": "Large text on solid background, no avatar. For name reveals and concept statements.",
    }

    for tid, t in templates.items():
        if tid in split_map:
            t["split_ratio"] = split_map[tid]["ratio"]
            t["background"] = split_map[tid]["bg"]
        if tid in desc_map:
            t["description"] = desc_map[tid]

    # Build the template class mapping (ANCHOR vs PROOF)
    anchor_templates = {"logo-reveal-split", "avatar-overlay", "avatar-direct"}
    for tid, t in templates.items():
        t["template_class"] = "ANCHOR" if tid in anchor_templates else "PROOF"

    registry = {
        "_derived_from": [ex["meta"]["source_video"] for ex in examples],
        "_derived_at": "auto-generated by derive_style_pack.py",
        "templates": templates,
        "template_class_map": {
            "ANCHOR": sorted([tid for tid, t in templates.items() if t["template_class"] == "ANCHOR"]),
            "PROOF": sorted([tid for tid, t in templates.items() if t["template_class"] == "PROOF"]),
        },
    }

    return registry


def derive_rhythm_bounds(examples):
    """
    Extract min/max rhythm metrics from training examples for QA validation.
    As more examples are added, these bounds widen to reflect observed range.
    """
    metrics = {
        "avg_visual_change_s": [],
        "avatar_on_screen_pct": [],
        "caption_suppression_pct": [],
        "max_static_hold_s": [],
        "total_visual_states": [],
        "template_types_used": [],
        "scene_cuts_per_minute": [],
        "words_per_second": [],
    }

    for ex in examples:
        rd = ex["completion"].get("rhythm_data", {})
        dur = ex["meta"]["duration_s"]

        if "avg_visual_change_s" in rd:
            metrics["avg_visual_change_s"].append(rd["avg_visual_change_s"])
        if "avatar_on_screen_pct" in rd:
            metrics["avatar_on_screen_pct"].append(rd["avatar_on_screen_pct"])
        if "caption_suppression_pct" in rd:
            metrics["caption_suppression_pct"].append(rd["caption_suppression_pct"])
        if "max_static_hold_s" in rd:
            metrics["max_static_hold_s"].append(rd["max_static_hold_s"])
        if "total_visual_states" in rd:
            metrics["total_visual_states"].append(rd["total_visual_states"])
        if "template_types_used" in rd:
            metrics["template_types_used"].append(rd["template_types_used"])
        if "scene_cuts_detected" in rd:
            metrics["scene_cuts_per_minute"].append(rd["scene_cuts_detected"] / (dur / 60))
        if "words_per_second" in rd:
            metrics["words_per_second"].append(rd["words_per_second"])

    # Compute bounds — for single example, use as both min and max with 20% margin
    bounds = {}
    for key, values in metrics.items():
        if not values:
            continue
        mn, mx = min(values), max(values)
        margin = max(abs(mn) * 0.2, 0.5)
        bounds[key] = {
            "min": round(mn - margin, 1),
            "max": round(mx + margin, 1),
            "observed": [round(v, 1) for v in values],
            "n_examples": len(values),
        }

    # Template oscillation bounds
    max_proof_run = 0
    max_anchor_run = 0
    for ex in examples:
        seq = ex["completion"].get("template_class_sequence", [])
        if not seq:
            continue
        current_class = seq[0]
        run = 1
        for cls in seq[1:]:
            if cls == current_class:
                run += 1
            else:
                if current_class == "PROOF":
                    max_proof_run = max(max_proof_run, run)
                else:
                    max_anchor_run = max(max_anchor_run, run)
                current_class = cls
                run = 1
        # Final run
        if current_class == "PROOF":
            max_proof_run = max(max_proof_run, run)
        else:
            max_anchor_run = max(max_anchor_run, run)

    # Proof escalation arcs observed
    proof_arcs = []
    for ex in examples:
        arc = ex["completion"].get("proof_escalation", [])
        if arc:
            proof_arcs.append(arc)

    result = {
        "_derived_from": [ex["meta"]["source_video"] for ex in examples],
        "_derived_at": "auto-generated by derive_style_pack.py",
        "metric_bounds": bounds,
        "oscillation": {
            "max_consecutive_proof_segments": max_proof_run,
            "max_consecutive_anchor_segments": max_anchor_run,
            "recommended_max_proof_run": min(max_proof_run + 1, 5),
            "recommended_max_anchor_run": min(max_anchor_run + 1, 4),
        },
        "proof_arcs_observed": proof_arcs,
    }

    return result


def derive_caption_modes(examples):
    """
    Extract caption mode definitions and suppression rules from training examples.
    """
    # Collect all caption styles seen
    styles_seen = []
    suppression_zones = []
    emphasis_rules = []

    for ex in examples:
        cd = ex["completion"].get("caption_data", {})
        if "style" in cd:
            styles_seen.append(cd["style"])
        for zone in cd.get("suppression_zones", []):
            zone["source"] = ex["meta"]["creator"]
            suppression_zones.append(zone)
        for rule in cd.get("emphasis_rules", []):
            rule["source"] = ex["meta"]["creator"]
            emphasis_rules.append(rule)

    # Define caption modes based on what we've observed
    modes = {
        "standard": {
            "description": "Default subtitle captions in bottom safe zone",
            "position_y_pct": 85,
            "font_size_pt": 42,
            "case": "mixed",
            "outline": "2px #000",
            "used_by_templates": ["split-screen-standard"],
        },
        "headline": {
            "description": "Large persuasion headlines at proof/presenter boundary. NOT subtitles.",
            "position_y_pct": 55,
            "font_size_pt": 90,
            "case": "ALL_CAPS",
            "font_family": "condensed bold sans-serif",
            "outline": "4px #000000",
            "shadow": "2px 2px 4px rgba(0,0,0,0.8)",
            "max_words_per_chunk": 4,
            "used_by_templates": [
                "logo-reveal-split",
                "proof-overlay-split",
                "avatar-overlay",
                "proof-fullscreen-warm",
                "text-fullscreen-dark",
                "avatar-direct",
            ],
        },
        "suppressed": {
            "description": "No captions rendered. UI text on screen carries the meaning.",
            "position_y_pct": None,
            "font_size_pt": 0,
            "used_by_templates": ["card-carousel", "demo-fullscreen"],
        },
        "section-label": {
            "description": "Bold section marker (plugin name, chapter title). Uses headline style with inverted colors.",
            "position_y_pct": 55,
            "font_size_pt": 90,
            "case": "ALL_CAPS",
            "color": "#000000",
            "outline": "4px #FFFFFF",
            "used_by_templates": ["proof-fullscreen-warm", "proof-overlay-split"],
        },
        "badge-overlay": {
            "description": "Caption text rendered as floating badge/pill overlay on presenter body, not as text line.",
            "position_y_pct": None,
            "font_size_pt": 64,
            "render_as": "badge-component",
            "used_by_templates": ["avatar-overlay"],
        },
    }

    # Suppression rules — when to suppress captions
    suppression_rules = [
        {
            "condition": "template is demo-fullscreen",
            "action": "suppress all captions",
            "reason": "Cursor interaction + UI text carries all meaning; captions obstruct",
        },
        {
            "condition": "template is card-carousel",
            "action": "suppress all captions",
            "reason": "Cards contain their own readable title + description text",
        },
        {
            "condition": "visual contains dense readable text (document, code, spreadsheet)",
            "action": "suppress OR reduce to section-label only",
            "reason": "Two text layers compete for attention",
        },
    ]

    # Deduplicate emphasis rules
    seen_patterns = set()
    unique_emphasis = []
    for rule in emphasis_rules:
        pattern = rule.get("pattern", "")
        if pattern not in seen_patterns:
            seen_patterns.add(pattern)
            unique_emphasis.append(rule)

    result = {
        "_derived_from": [ex["meta"]["source_video"] for ex in examples],
        "_derived_at": "auto-generated by derive_style_pack.py",
        "modes": modes,
        "suppression_rules": suppression_rules,
        "emphasis_rules": unique_emphasis,
        "template_to_caption_mode": {},
    }

    # Build the template → caption mode lookup
    for mode_id, mode in modes.items():
        for tmpl in mode.get("used_by_templates", []):
            result["template_to_caption_mode"][tmpl] = mode_id

    return result


def main():
    parser = argparse.ArgumentParser(description="Derive style pack from training examples")
    parser.add_argument("--example", help="Path to specific training-example.json")
    args = parser.parse_args()

    DERIVED_DIR.mkdir(exist_ok=True)

    print("Loading training examples...")
    examples = load_examples(args.example)
    if not examples:
        print("No complete training examples found.")
        sys.exit(1)
    print(f"  Loaded {len(examples)} example(s)")

    print("\nDeriving template registry...")
    registry = derive_template_registry(examples)
    registry_path = DERIVED_DIR / "template-registry.json"
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"  {len(registry['templates'])} templates → {registry_path}")

    print("\nDeriving rhythm bounds...")
    bounds = derive_rhythm_bounds(examples)
    bounds_path = DERIVED_DIR / "rhythm-bounds.json"
    with open(bounds_path, "w", encoding="utf-8") as f:
        json.dump(bounds, f, indent=2, ensure_ascii=False)
    print(f"  {len(bounds['metric_bounds'])} metrics → {bounds_path}")

    print("\nDeriving caption modes...")
    captions = derive_caption_modes(examples)
    captions_path = DERIVED_DIR / "caption-modes.json"
    with open(captions_path, "w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2, ensure_ascii=False)
    print(f"  {len(captions['modes'])} modes → {captions_path}")

    print("\nDone. Derived artifacts in:", DERIVED_DIR)
    print("\nNext: Reference these files from:")
    print("  - styles/proof-escalation-editorial.md")
    print("  - .claude/rules/template-grammar.md")
    print("  - .claude/rules/qa-gates.md (validation thresholds)")


if __name__ == "__main__":
    main()
