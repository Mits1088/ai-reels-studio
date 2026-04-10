import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * FlashReset — 2-3 frame white flash overlay between major sections.
 *
 * Used in the editorial-authority style as a visual palate cleanser
 * between proof blocks. Place in its own <Sequence> at section boundaries.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const FlashReset: React.FC<{
  durationInFrames?: number;
  color?: string;
  peakOpacity?: number;
}> = ({
  durationInFrames = 3,
  color = "#FFFFFF",
  peakOpacity = 1.0,
}) => {
  const frame = useCurrentFrame();

  // Build dynamic input/output ranges based on duration
  const opacity =
    durationInFrames <= 2
      ? // 2-frame flash: instant peak then fade
        interpolate(frame, [0, 1, 2], [peakOpacity, peakOpacity * 0.4, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : // 3-frame flash: peak → half → gone
        interpolate(
          frame,
          [0, 1, 2, 3],
          [peakOpacity, peakOpacity, peakOpacity * 0.5, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity,
        zIndex: 100,
        pointerEvents: "none",
      }}
    />
  );
};
