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
  display?: "responsive" | "center-full" | "hook-reveal" | "bg";
  loop?: boolean;
  playbackRate?: number;
  clipStartTime?: number;
  punchFrame?: number;
  notes?: string;
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
