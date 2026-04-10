import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * FocusVignette — Animated vignette that intensifies for emphasis.
 * Darkens edges to draw focus to center content. Can animate intensity.
 *
 * Props:
 * - intensity: base vignette strength (0-1)
 * - pulseAmount: how much it pulses
 * - color: vignette edge color
 * - focusX, focusY: center of the bright area (percent)
 */
export const FocusVignette: React.FC<{
  intensity?: number;
  pulseAmount?: number;
  color?: string;
  focusX?: number;
  focusY?: number;
  durationInFrames?: number;
}> = ({
  intensity = 0.6,
  pulseAmount = 0.15,
  color = "rgba(0, 0, 0",
  focusX = 50,
  focusY = 45,
}) => {
  const frame = useCurrentFrame();

  // Subtle pulse
  const pulse = intensity + Math.sin(frame * 0.04) * pulseAmount;
  const strength = Math.min(1, Math.max(0, pulse));

  return (
    <AbsoluteFill
      style={{
        zIndex: 3,
        pointerEvents: "none",
        background: `radial-gradient(ellipse at ${focusX}% ${focusY}%,
          transparent 30%,
          ${color}, ${strength * 0.3}) 55%,
          ${color}, ${strength * 0.6}) 75%,
          ${color}, ${strength * 0.85}) 100%)`,
      }}
    />
  );
};
