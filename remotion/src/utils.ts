import { interpolate } from "remotion";
import type { TimelineEntry } from "./types";

export const FPS = 30;

// ── Split-screen layout contract ──────────────────────────────────────────────
// These two values are the single source of truth for the split-screen boundary.
// AvatarVideo imports SPLIT_HEIGHT_PCT.
// ALL content containers in the top zone must use CONTENT_HEIGHT_PCT.
// If you change one, the other changes automatically — never hardcode "60%" or "40%".
export const SPLIT_HEIGHT_PCT = 60;                          // avatar bottom zone
export const CONTENT_HEIGHT_PCT = 100 - SPLIT_HEIGHT_PCT;   // content top zone (40%)

export const toFrame = (seconds: number) => Math.round(seconds * FPS);

export function getAvatarLayout(
  entries: TimelineEntry[],
  currentTimeSec: number
): { layout: string; entry: TimelineEntry } | null {
  for (const entry of entries) {
    if (currentTimeSec >= entry.start && currentTimeSec < entry.end) {
      return { layout: entry.layout || "full-screen", entry };
    }
  }
  return null;
}

export function hardOpacity(frame: number, dur: number, fadeIn: number, fadeOut: number): number {
  if (frame <= 0 || frame >= dur - 1) return 0;
  const enter = fadeIn > 0
    ? interpolate(frame, [0, fadeIn], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 1;
  const exit = fadeOut > 0
    ? interpolate(frame, [dur - 1 - fadeOut, dur - 1], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 1;
  return enter * exit;
}
