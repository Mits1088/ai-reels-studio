# Proof Escalation Editorial

Style ID: `proof-escalation-editorial`

A proof-led editorial style where every section answers the next viewer objection. Visual sophistication comes from template sequencing and proof grammar, not transitions.

Derived from reference analysis. Machine-readable source of truth:
- `training/derived/template-registry.json`
- `training/derived/rhythm-bounds.json`
- `training/derived/caption-modes.json`

---

## When to use

- Product launches, feature announcements, capability showcases
- Reels that need to prove a tool works, not just describe it
- Audience: business professionals who need to see real output, not hype
- Duration: 40–60s (proof arcs need space)

---

## Proof Escalation Arc

Every reel using this style must declare its proof arc during scripting. Each section answers the next viewer objection:

| Stage | Objection it answers | Typical visual |
|---|---|---|
| **existence** | "Does this exist?" | Product UI, logo, landing page |
| **breadth** | "Is it just one thing?" | Card carousel, icon bar, list |
| **process** | "Does it actually work?" | Live UI demo, install flow, cursor interaction |
| **output** | "What does it produce?" | Real screenshots of actual output (Excel, PPTX, reports) |
| **authority** | "Can I trust it?" | Verified badges, trust overlays, credibility markers |
| **cta** | "Where do I get it?" | DM prompt, follow, link |

Not every reel needs all 6 stages. The minimum is: existence → output → cta. But stages must progress forward — never loop back.

---

## Template System

This style uses **layout templates** instead of per-beat component selection. Each beat selects a template ID from the registry. The template controls avatar visibility, split ratio, background, and caption behavior simultaneously.

Template definitions: `training/derived/template-registry.json`

### Allowed templates

| Template | Class | Avatar | Split | Caption | Use for |
|---|---|---|---|---|---|
| `logo-reveal-split` | ANCHOR | bottom 50% | 50/50 | headline | Hook with brand logo |
| `proof-overlay-split` | PROOF | bottom peek 35% | 65/35 | headline | Screenshot proof with face presence |
| `card-carousel` | PROOF | hidden | 100/0 | suppressed | Rapid category/feature listing |
| `demo-fullscreen` | PROOF | hidden | 100/0 | suppressed | Live UI recording |
| `avatar-overlay` | ANCHOR | full, overlays ON body | 0/100 | headline or badge | Trust, integration, CTA |
| `proof-fullscreen-warm` | PROOF | hidden | 100/0 | section-label | Output proof on warm bg |
| `text-fullscreen-dark` | PROOF | hidden | 100/0 | headline | Document/text proof |
| `avatar-direct` | ANCHOR | full, clean | 0/100 | headline | Direct address, pattern interrupt, close |

### Template class oscillation

Templates are classified as ANCHOR (face-led) or PROOF (content-led). The reel must oscillate between them:

- Max consecutive PROOF segments: **4** (from `rhythm-bounds.json`)
- Max consecutive ANCHOR segments: **4**
- After a PROOF burst > 3 segments, the next segment must be ANCHOR
- Longest avatar absence: ~11s (compensated by constant cursor/interaction motion)

### Split ratios

This style uses **flexible split ratios** per template, not a fixed 40/60:

| Ratio | When |
|---|---|
| 50/50 | Hook logo reveal |
| 65/35 | Proof screenshot with presenter peek |
| 100/0 | Demo fullscreen, card carousel, output proof (avatar hidden) |
| 0/100 | Avatar direct address, avatar with overlays |

The standard 40/60 split is NOT used in this style. If content needs a split, use 65/35 (proof-overlay-split) to give proof more weight.

---

## Caption Modes

Caption definitions: `training/derived/caption-modes.json`

This style does NOT use standard subtitle captions. It has 5 caption modes:

### headline (default for most templates)
- 80–100pt condensed bold sans-serif, ALL CAPS
- White fill, 4px black stroke, drop shadow
- Positioned at y:55% — the boundary between proof content and presenter
- Max 4 words per chunk, ~1s per chunk
- These are persuasion weapons, not subtitles

### suppressed (demo-fullscreen, card-carousel)
- No captions rendered
- Activated when: UI text is readable on screen, cursor interaction tells the story, cards have their own text
- **Rule**: if the visual already contains readable text, suppress the caption layer

### section-label (proof sections)
- Same size as headline, but inverted: black fill, white outline
- Used when naming a proof section: "FINANCE PLUGIN", "OPERATIONS PLUGIN"
- Functions as a chapter marker, not transcription

### badge-overlay (avatar-overlay)
- Caption text rendered as floating badge/pill component on presenter body
- Used for trust markers: "REVIEWED", "SAFE"
- Not a text line — a visual element

### standard (fallback)
- Bottom safe zone, ~42pt, mixed case
- Only used if this style is mixed with cinematic-presenter elements

### Emphasis rules
- **Negated concept**: RED (#FF3333). Example: "GENERIC" when the narrator says "instead of getting generic"
- **Plugin/tool name as section label**: inverted colors (black fill, white stroke)
- **Trust keyword**: rendered as badge-overlay, not text

---

## Rhythm Targets

Thresholds: `training/derived/rhythm-bounds.json`

| Metric | Target range | Source |
|---|---|---|
| Visual change frequency | every 2.6–3.8s | avg_visual_change_s |
| Avatar on-screen | 38–58% | avatar_on_screen_pct |
| Caption suppression | 24–36% of reel duration | caption_suppression_pct |
| Max static hold | 1.5–2.5s | max_static_hold_s |
| Visual states | 14–22 per reel | total_visual_states |
| Template types used | 6–10 | template_types_used |
| Scene cuts per minute | 8–12 | scene_cuts_per_minute |

These bounds will widen as more training examples are annotated.

---

## Backgrounds

| Template class | Background |
|---|---|
| PROOF with warm content (screenshots, output) | Warm beige (#F0EBE0) |
| PROOF with dark content (UI, documents, cards) | Dark (#1A1A1A) |
| ANCHOR (avatar direct/overlay) | Natural (real environment) or warm beige |

No Aurora, GradientMesh, or BackgroundBeams. Backgrounds are solid or natural — sophistication comes from content, not atmospheric effects.

---

## Transitions

Hard cut between all templates. No wipe, fade, scale, or blend transitions.

The reel's sophistication is in **template sequencing and proof grammar**, not in transition effects. If a viewer notices the cut, the content failed — not the transition.

---

## Components required

Existing components that map to this style: AvatarVideo, FramedImage, BRollVideo, OverlayKeyword, BadgePopup, HeroTextCard, Caption.

New components needed (build on demand, not preemptively):

| Component | Template | Status |
|---|---|---|
| `CardCarousel` | card-carousel | NOT BUILT — use ChapterDivider sequence as interim |
| `ConnectorIconBar` | avatar-overlay | NOT BUILT — use inline JSX |
| `AnimatedChecklist` | avatar-overlay | NOT BUILT — use inline JSX |
| `HeadlineCaption` | all headline-mode templates | NOT BUILT — extend existing Caption |

---

## Pipeline integration

### Phase 1 (reel-script)
Script declares `proof_arc` — ordered list of proof classes the reel will cover.

### Phase 4b-i (shot-list visual assignment)
Each beat gets a `template_id` from the registry. Template determines avatar, split, background, caption mode.

### Phase 4b-ii (component mapping)
Template constrains component choice. Validate template → component compatibility.

### Phase 5 (assembly)
Timeline.json entries include: `template_id`, `captionMode`, `splitRatio`. Assembly reads these instead of inferring layout from display mode alone.

### Phase 6 (QA)
Validate against rhythm-bounds.json: oscillation, suppression coverage, proof arc order, visual state count.

---

## Precedence

When `proof-escalation-editorial` is active:
1. Template registry (training/derived/template-registry.json) overrides per-component selection
2. Caption modes override standard subtitle behavior
3. Split ratios are template-driven, not style-global
4. Rhythm bounds from training data override baseline QA thresholds
5. Baseline rules (timing-sync, qa-gates blocking checks) still apply
