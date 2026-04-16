# Beat Fragment Library

Equivalent to the Remotion skills system's "example skills" — complete, validated
timeline.json fragments for proven beat patterns.

## How to use

During Phase 5 (assembly), instead of constructing timeline entries from scratch,
look up the fragment that most closely matches the beat and adapt it.

```bash
python -m lib.beat_fragments list
python -m lib.beat_fragments show editorial-hook-scrolling-grid
python -m lib.beat_fragments show cinematic-number-proof
```

## Adding new fragments

After a reel renders and passes QA, extract any beat that worked particularly well
and save it as a fragment here. The fragment becomes a reusable reference.

Fragment file format:
- One JSON file per pattern
- Filename: `{style}-{classification}-{variant}.json`
- Required fields: id, style, classification, description, notes, timeline_fragment

## Available fragments

| ID | Style | Classification | Description |
|---|---|---|---|
| editorial-hook-scrolling-grid | editorial-authority | hook_opening | ScrollingIconGrid hook with split-screen avatar |
| editorial-number-proof | editorial-authority | number_proof_with_asset | FramedImage + OverlayKeyword proof beat |
| editorial-section-flash | editorial-authority | section_transition | 9-frame FlashReset section divider |
| cinematic-hook-logo-reveal | cinematic-presenter | hook_opening | Logo bounce hook with FramedImage split |
| cinematic-number-popup | cinematic-presenter | number_proof_no_asset | NumberPopup on full-screen avatar |
| cinematic-cta-dark | cinematic-presenter | cta | Dark GradientMesh CTA with OverlayKeyword |
