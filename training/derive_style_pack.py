"""
Derive Style Pack

Reads training-example.json files and produces machine-readable derived artifacts
that the rest of the pipeline consumes. This is the single translation layer between
training data and repo rules/skills/assembly.

Usage:
    python training/derive_style_pack.py
    python training/derive_style_pack.py --example training/references/nicholas-processed/training-example.json
    python training/derive_style_pack.py --only taste-rules
    python training/derive_style_pack.py --only template-registry,rhythm-bounds

Outputs (to training/derived/):
    template-registry.json   — template definitions with avatar/split/caption/bg behavior
    rhythm-bounds.json       — min/max thresholds for QA validation
    caption-modes.json       — headline mode spec, suppression rules, emphasis rules
    taste-rules.json         — qualitative taste guidance: hook patterns, proof patterns, anti-patterns
                               Confidence is LOW when n_examples < 3. Read alongside creative-feedback.json.

SPARSE DATA WARNING:
    Taste rules derived from fewer than 3 complete, annotated examples are LOW CONFIDENCE.
    They inform planning but should not override creative-feedback.json or body-grammar rules.
    Add more annotated examples to raise confidence. See training/README-feedback-annotation.md.
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


def _load_reference_strengths():
    """Return {creator: reference_strength} from training-index.json."""
    if not INDEX_PATH.exists():
        return {}
    with open(INDEX_PATH) as f:
        idx = json.load(f)
    return {entry["creator"]: entry.get("reference_strength", "unrated")
            for entry in idx.get("examples", [])}


def _evidence_type(ta):
    """Map annotation_source to evidence_type string."""
    src = ta.get("annotation_source", "")
    return {"human": "human_annotation", "mixed": "mixed"}.get(src, "machine_inferred")


def _make_entry(text, field, creator, ta, ref_strength):
    """Build a pattern entry with full provenance."""
    return {
        field: text,
        "source_example": creator,
        "evidence_type": _evidence_type(ta),
        "reference_strength": ref_strength,
    }


def derive_taste_rules(examples):
    """
    Aggregate qualitative taste guidance from taste_annotation blocks.

    Positive pattern lists (hook, proof, body, motion, caption, creative_principles)
    are populated only from examples with reference_strength == "strong".  This
    prevents a single creator's pacing or style from becoming the system default
    via an "unrated" or "weak" example.

    Anti-patterns are populated from ALL reference strengths — weak examples are
    valuable precisely because they teach what not to repeat.

    Per-entry provenance fields:
        evidence_type      — human_annotation | machine_inferred | mixed
        source_example     — creator identifier from meta.creator
        reference_strength — strong | weak | unrated (from training-index.json)

    Top-level confidence levels (based on n_annotated strong examples):
        high   — 3+ complete/partial annotated strong examples
        medium — 2
        low    — 0 or 1  (sparse data warning active)
    """
    ref_strengths = _load_reference_strengths()

    # Only strongly-annotated examples contribute to positive patterns
    strong_annotated = [
        ex for ex in examples
        if ex.get("taste_annotation", {}).get("annotation_completeness") in ("complete", "partial")
        and ref_strengths.get(ex["meta"]["creator"], "unrated") == "strong"
    ]
    # All annotated examples (any reference_strength) contribute anti-patterns
    all_annotated = [
        ex for ex in examples
        if ex.get("taste_annotation", {}).get("annotation_completeness") in ("complete", "partial")
    ]

    n = len(strong_annotated)
    confidence = "high" if n >= 3 else "medium" if n == 2 else "low"

    hook_patterns = []
    proof_patterns = []
    body_patterns = []
    motion_patterns = []
    caption_patterns = []
    anti_patterns = []
    creative_principles = []
    why_works_notes = []

    for ex in strong_annotated:
        ta = ex.get("taste_annotation", {})
        creator = ex["meta"]["creator"]
        ref = ref_strengths.get(creator, "unrated")

        def entry(text, field="pattern"):
            return _make_entry(text, field, creator, ta, ref)

        if ta.get("why_it_works"):
            why_works_notes.append(entry(ta["why_it_works"], "note"))
        if ta.get("hook_strength_reason"):
            hook_patterns.append(entry(ta["hook_strength_reason"], "principle"))
        if ta.get("proof_quality_notes"):
            proof_patterns.append(entry(ta["proof_quality_notes"], "principle"))
        if ta.get("body_variation_reason"):
            body_patterns.append(entry(ta["body_variation_reason"], "principle"))
        if ta.get("motion_quality_notes"):
            motion_patterns.append(entry(ta["motion_quality_notes"], "principle"))
        if ta.get("caption_quality_notes"):
            caption_patterns.append(entry(ta["caption_quality_notes"], "principle"))

        for pattern in ta.get("repeatable_patterns", []):
            p_lower = pattern.lower()
            e = entry(pattern)
            if any(w in p_lower for w in ["hook", "first", "open", "scroll", "stop"]):
                hook_patterns.append(e)
            elif any(w in p_lower for w in ["proof", "screenshot", "evidence", "visual", "show"]):
                proof_patterns.append(e)
            elif any(w in p_lower for w in ["motion", "zoom", "still", "ambient", "drift", "camera"]):
                motion_patterns.append(e)
            elif any(w in p_lower for w in ["caption", "suppres", "text overlay", "subtitle"]):
                caption_patterns.append(e)
            else:
                body_patterns.append(e)

        for takeaway in ta.get("creative_takeaways", []):
            creative_principles.append(entry(takeaway, "principle"))

    # Anti-patterns: all annotated regardless of reference_strength
    for ex in all_annotated:
        ta = ex.get("taste_annotation", {})
        creator = ex["meta"]["creator"]
        ref = ref_strengths.get(creator, "unrated")
        for pattern in ta.get("avoid_patterns", []):
            anti_patterns.append(_make_entry(pattern, "pattern", creator, ta, ref))

    sparse_warning = (
        "SPARSE DATA WARNING: Positive taste rules are derived from fewer than 3 strongly-rated "
        "annotated examples. Confidence is LOW. These rules may influence candidate ranking "
        "but must not override creative-feedback.json entries, establish default hook/body "
        "templates, or block choices that creative-feedback.json permits. "
        "See training/README-feedback-annotation.md to raise confidence."
    ) if confidence == "low" else None

    usage_constraints = {
        "low": {
            "allowed": [
                "influence candidate ranking in component and hook selection",
                "suggest alternative hook angles when creative-feedback.json is silent",
                "inform anti-pattern checks before finalizing any section"
            ],
            "blocked": [
                "override any entry in creative-feedback.json",
                "establish a default hook archetype or body template",
                "block a component or motion choice that creative-feedback.json permits",
                "set planning defaults for script, shot-list, or motion-intent phases"
            ]
        },
        "medium": {
            "allowed": [
                "all low-confidence uses",
                "inform soft preference defaults when creative-feedback.json is silent on a topic"
            ],
            "blocked": [
                "override hard_rules in creative-feedback.json",
                "establish mandatory templates or required ordering"
            ]
        },
        "high": {
            "allowed": [
                "all medium-confidence uses",
                "treated on par with soft_preferences in creative-feedback.json when not contradicted"
            ],
            "blocked": [
                "override hard_rules in creative-feedback.json"
            ]
        }
    }

    # Summary of how each example contributes (for transparency)
    contribution_map = {}
    for ex in examples:
        creator = ex["meta"]["creator"]
        ta = ex.get("taste_annotation", {})
        completeness = ta.get("annotation_completeness", "none")
        ref = ref_strengths.get(creator, "unrated")
        if ref == "strong" and completeness in ("complete", "partial"):
            role = "positive_patterns_and_anti_patterns"
        elif completeness in ("complete", "partial"):
            role = "anti_patterns_only"
        else:
            role = "no_contribution_until_annotated"
        contribution_map[creator] = {
            "reference_strength": ref,
            "annotation_completeness": completeness,
            "contribution": role,
        }

    result = {
        "_derived_from": [ex["meta"]["source_video"] for ex in examples],
        "_annotated_examples": [ex["meta"]["creator"] for ex in strong_annotated],
        "_derived_at": "auto-generated by derive_style_pack.py",
        "_confidence": confidence,
        "_n_annotated": n,
        "_sparse_data_warning": sparse_warning,
        "_usage_note": (
            "Read alongside memory/creative-feedback.json (first-person accumulated taste) "
            "and .claude/rules/body-grammar.md (structural rules). "
            "This file captures WHAT makes liked reference reels work — third-person patterns "
            "extracted from external reels. creative-feedback.json wins when they conflict "
            "unless this file's _confidence is 'high'."
        ),
        "_usage_constraints": usage_constraints,
        "_contribution_by_example": contribution_map,
        "why_it_works": why_works_notes,
        "hook_patterns": hook_patterns,
        "proof_patterns": proof_patterns,
        "body_patterns": body_patterns,
        "motion_patterns": motion_patterns,
        "caption_patterns": caption_patterns,
        "anti_patterns": anti_patterns,
        "creative_principles": creative_principles,
    }

    return result


ALL_OUTPUTS = ["template-registry", "rhythm-bounds", "caption-modes", "taste-rules"]


def main():
    parser = argparse.ArgumentParser(description="Derive style pack from training examples")
    parser.add_argument("--example", help="Path to specific training-example.json")
    parser.add_argument(
        "--only",
        help="Comma-separated list of outputs to regenerate. "
             f"Options: {', '.join(ALL_OUTPUTS)}",
    )
    args = parser.parse_args()

    only = set(x.strip() for x in args.only.split(",")) if args.only else set(ALL_OUTPUTS)
    invalid = only - set(ALL_OUTPUTS)
    if invalid:
        print(f"Unknown --only values: {', '.join(sorted(invalid))}")
        print(f"Valid options: {', '.join(ALL_OUTPUTS)}")
        sys.exit(1)

    DERIVED_DIR.mkdir(exist_ok=True)

    print("Loading training examples...")
    examples = load_examples(args.example)
    if not examples:
        print("No complete training examples found.")
        sys.exit(1)
    print(f"  Loaded {len(examples)} example(s)")

    if "template-registry" in only:
        print("\nDeriving template registry...")
        registry = derive_template_registry(examples)
        registry_path = DERIVED_DIR / "template-registry.json"
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        print(f"  {len(registry['templates'])} templates → {registry_path}")

    if "rhythm-bounds" in only:
        print("\nDeriving rhythm bounds...")
        bounds = derive_rhythm_bounds(examples)
        bounds_path = DERIVED_DIR / "rhythm-bounds.json"
        with open(bounds_path, "w", encoding="utf-8") as f:
            json.dump(bounds, f, indent=2, ensure_ascii=False)
        print(f"  {len(bounds['metric_bounds'])} metrics → {bounds_path}")

    if "caption-modes" in only:
        print("\nDeriving caption modes...")
        captions = derive_caption_modes(examples)
        captions_path = DERIVED_DIR / "caption-modes.json"
        with open(captions_path, "w", encoding="utf-8") as f:
            json.dump(captions, f, indent=2, ensure_ascii=False)
        print(f"  {len(captions['modes'])} modes → {captions_path}")

    if "taste-rules" in only:
        print("\nDeriving taste rules...")
        taste = derive_taste_rules(examples)
        taste_path = DERIVED_DIR / "taste-rules.json"
        with open(taste_path, "w", encoding="utf-8") as f:
            json.dump(taste, f, indent=2, ensure_ascii=False)
        n_patterns = sum(
            len(taste[k])
            for k in ["hook_patterns", "proof_patterns", "body_patterns",
                       "motion_patterns", "caption_patterns", "anti_patterns",
                       "creative_principles"]
        )
        print(f"  {n_patterns} patterns ({taste['_confidence']} confidence, "
              f"{taste['_n_annotated']} annotated) → {taste_path}")
        if taste["_sparse_data_warning"]:
            print(f"\n  ⚠  {taste['_sparse_data_warning']}")

    print("\nDone. Derived artifacts in:", DERIVED_DIR)
    print("\nNext: Reference these files from:")
    print("  - styles/proof-escalation-editorial.md")
    print("  - .claude/rules/template-grammar.md")
    print("  - .claude/rules/qa-gates.md (validation thresholds)")
    print("  - training/derived/taste-rules.json (consult before planning phases)")


if __name__ == "__main__":
    main()
