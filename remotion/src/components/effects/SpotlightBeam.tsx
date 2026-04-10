import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * SpotlightBeam — Focused light beam that illuminates a target area.
 * Great for drawing attention to demos, reveals, and key content.
 *
 * Props:
 * - x, y: beam target position (0-100 percent)
 * - size: beam diameter
 * - color: beam tint
 * - fadeInFrames: how quickly beam appears
 * - sway: subtle movement amplitude
 */
export const SpotlightBeam: React.FC<{
  x?: number;
  y?: number;
  size?: number;
  color?: string;
  fadeInFrames?: number;
  sway?: number;
  durationInFrames: number;
}> = ({
  x = 50,
  y = 40,
  size = 40,
  color = "rgba(0, 229, 255, 0.08)",
  fadeInFrames = 4,
  sway = 3,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, fadeInFrames, durationInFrames - 3, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Subtle organic sway
  const swayX = x + Math.sin(frame * 0.04) * sway;
  const swayY = y + Math.cos(frame * 0.03) * sway * 0.6;

  return (
    <AbsoluteFill style={{ zIndex: 2, pointerEvents: "none", opacity }}>
      {/* Main beam cone from top */}
      <div
        style={{
          position: "absolute",
          left: `${swayX - size / 2}%`,
          top: 0,
          width: `${size}%`,
          height: `${swayY + 20}%`,
          background: `linear-gradient(180deg,
            rgba(255, 255, 255, 0.02) 0%,
            ${color} 60%,
            transparent 100%)`,
          clipPath: `polygon(40% 0%, 60% 0%, 100% 100%, 0% 100%)`,
        }}
      />
      {/* Ground glow where beam hits */}
      <div
        style={{
          position: "absolute",
          left: `${swayX - size * 0.4}%`,
          top: `${swayY - 5}%`,
          width: `${size * 0.8}%`,
          height: `${size * 0.4}%`,
          borderRadius: "50%",
          background: `radial-gradient(ellipse, ${color}, transparent 70%)`,
        }}
      />
    </AbsoluteFill>
  );
};
