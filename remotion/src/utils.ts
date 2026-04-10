import { interpolate } from "remotion";
import type { TimelineEntry } from "./types";

export const FPS = 30;

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
