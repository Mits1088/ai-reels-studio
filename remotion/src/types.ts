export interface CaptionToken {
  text: string;
  fromMs: number;
  toMs: number;
}

export interface TransitionPreset {
  enter:
    | "punch" | "slide-up" | "slide-left" | "zoom-in" | "scale-pop"
    | "scale-pop-overshoot" | "glitch" | "fade" | "wipe-up"
    | "zoom-through" | "blur-dissolve" | "luminance-sweep" | "iris-reveal"
    | "whip-pan" | "smooth-push" | "hard-cut" | "flash-reset" | "slide-stack";
  exit:
    | "punch-out" | "slide-down" | "slide-right" | "scale-down"
    | "fade" | "wipe-down"
    | "zoom-through-out" | "blur-out" | "whip-out" | "iris-close"
    | "hard-cut";
  enterDur: number;
  exitDur: number;
  kenBurns?: boolean;
}

export interface ZoomMoment {
  at: number;       // seconds into the clip when zoom starts
  x: number;        // horizontal focus point (0–100% of the content)
  y: number;        // vertical focus point (0–100% of the content)
  scale: number;    // zoom level — 1.8 = 80% larger, 2.0 = 2× zoom
  holdFor?: number; // seconds to hold zoom before easing back out (default: holds to end)
}

export interface TimelineEntry {
  beat_id?: string;
  start: number;
  end: number;
  asset?: string;
  layout?: string;
  text?: string;
  transition?: { type: string; duration: number };
  transition_preset?: {
    enter: string;
    exit: string;
    enterDur: number;
    exitDur: number;
    kenBurns?: boolean;
  };
  zoom_moments?: ZoomMoment[];
  volume?: number;
  display?: "responsive" | "center-full" | "guided-demo" | "hook-reveal" | "bg" | "image-grid" | "scroll-image" | "app-window";
  /** Config for display:"app-window" — wraps the asset in macOS browser chrome */
  appWindow?: {
    platform?: "macos" | "chrome";
    theme?: "light" | "dark";
    url?: string;
    title?: string;
    showUrlBar?: boolean;
  };
  /** ImageGrid2x2 image list — required when display is "image-grid" */
  images?: Array<{ src: string }>;
  /** ScrollImage source aspect ratio (width/height) — required when display is "scroll-image" */
  imageAspectRatio?: number;
  /** ImageGrid2x2 per-cell spring stagger (frames). Default [0,5,10,15] */
  staggerDelays?: number[];
  /** ImageGrid2x2: cross-dissolve the grid in over 8 frames */
  dissolveFromPrevious?: boolean;
  /** ImageGrid2x2: cell index (0-3) to pan left→right during hold. -1 = none */
  bookSpreadIndex?: number;
  /** Ambient scale push for center-full images (no zoom_moment needed) */
  ambient_zoom?: { fromScale: number; toScale: number; targetX: number; targetY: number };
  /** Config for display:"guided-demo" — browser frame + virtual camera pan + spotlight highlight */
  guided_demo?: {
    url?: string;
    show_frame?: boolean;
    img_width?: number;   // original image width in px (for correct coordinate math)
    img_height?: number;  // original image height in px
    pan_moments?: Array<{ at: number; x: number; y: number }>;
    highlight_moments?: Array<{
      at: number;
      duration: number;
      /** IMAGE-SPACE percentages — % of original image dimensions, NOT screen space */
      region: { x: number; y: number; w: number; h: number };
      /** "border" = clean orange outline (default). "dim" = dark vignette spotlight. */
      highlight_style?: "border" | "dim";
      /** CSS color for the border annotation. Defaults to Claude orange. Only applies to "border" style. */
      highlight_color?: string;
    }>;
  };
  loop?: boolean;
  playbackRate?: number;
  clipStartTime?: number;
  punchFrame?: number;
  notes?: string;
  /** Word-level timing tokens from @remotion/captions createTikTokStyleCaptions.
   *  When present, Caption.tsx renders karaoke-style word highlighting.
   *  When absent, Caption.tsx falls back to frame-division (legacy). */
  tokens?: CaptionToken[];

  /** Optional explicit background color for the time range this entry covers.
   *  Used by GenericReelComposition's getBackgroundAtTime helper to drive
   *  per-beat background color (e.g. proof-escalation-editorial warm beige
   *  #FAF9F5 vs cinematic-presenter white #FFFFFF). Falls back to layout-
   *  derived defaults when omitted. */
  bgColor?: string;

  // ── Editorial planning fields (Phase A — type-only, additive) ──────────
  // Populated by the edit-plan compiler (Phase C, lib/edit_plan/compile.py)
  // so the rendered timeline carries its template + proof + caption-mode
  // context for downstream tooling (critic, QA, learning, retrieval).
  //
  // GenericReelComposition does NOT consume these yet — they pass through
  // unchanged. The JSON schema (lib/schemas/timeline.schema.json) will
  // catch up in Phase C alongside the compiler. lib/grammar/ is the
  // runtime source of truth for the proof_class and captionMode enums.
  template_id?: string;
  proof_class?:
    | "existence"
    | "breadth"
    | "process"
    | "output"
    | "integration"
    | "authority"
    | "cta";
  avatar_mode?: string;
  splitRatio?: string;
  captionMode?:
    | "standard"
    | "headline"
    | "suppressed"
    | "section-label"
    | "badge-overlay";
  proof_protected?: boolean;
}

export interface OverlayEntry {
  beat_id?: string;
  type: string;
  start: number;
  end: number;
  asset?: string;
  props?: Record<string, unknown>;
  notes?: string;
}

export interface Timeline {
  total_duration: number;
  audio?: string;
  avatar_file?: string;
  lanes: {
    avatar: TimelineEntry[];
    demo: TimelineEntry[];
    broll?: TimelineEntry[];
    support: TimelineEntry[];
    captions: TimelineEntry[];
    sfx: TimelineEntry[];
    music: TimelineEntry[];
    overlays?: OverlayEntry[];
  };
}

// ── YouTube Pipeline Types ──────────────────────────────────────────

export interface YouTubeTimeline {
  total_duration: number;
  video: string;
  fps?: number;
  width?: number;
  height?: number;
  lanes: {
    overlays: OverlayEntry[];
    captions?: TimelineEntry[];
    sfx?: TimelineEntry[];
    music?: TimelineEntry[];
  };
}
