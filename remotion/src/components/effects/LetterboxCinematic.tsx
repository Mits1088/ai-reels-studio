import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * LetterboxCinematic — Black bars that slide in from top/bottom for dramatic moments.
 * Instantly makes any scene feel like a movie trailer. Great for hook and CTA.
 */
export const LetterboxCinematic: React.FC<{
  barHeight?: number;
  color?: string;
  durationInFrames: number;
}> = ({ barHeight = 120, color = "#000000", durationInFrames }) => {
  const frame = useCurrentFrame();

  const enter = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });
  const exit = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic),
  });
  const progress = Math.min(enter, exit);
  const offset = barHeight * progress;

  return (
    <AbsoluteFill style={{ zIndex: 52, pointerEvents: "none" }}>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        height: offset, background: color,
      }} />
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        height: offset, background: color,
      }} />
      {/* Subtle edge glow */}
      <div style={{
        position: "absolute", top: offset - 1, left: 0, right: 0,
        height: 1,
        background: "rgba(255,255,255,0.08)",
        opacity: progress,
      }} />
      <div style={{
        position: "absolute", bottom: offset - 1, left: 0, right: 0,
        height: 1,
        background: "rgba(255,255,255,0.08)",
        opacity: progress,
      }} />
    </AbsoluteFill>
  );
};
