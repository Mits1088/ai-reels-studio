import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * AnimatedDivider — Glowing line divider that draws itself.
 * Used between sections, list items, or as a decorative accent.
 * The line extends from center outward with a traveling glow.
 */
export const AnimatedDivider: React.FC<{
  color?: string;
  thickness?: number;
  width?: number;
  position?: "center" | number;
  durationInFrames: number;
}> = ({
  color = "#00E5FF",
  thickness = 2,
  width = 70,
  position = "center",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  // Line draws from center outward
  const drawProgress = interpolate(frame, [0, 5], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  // Traveling glow shimmer
  const shimmerX = (frame * 3) % 140 - 20;

  // Exit
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const lineWidth = width * drawProgress;
  const topVal = position === "center" ? "50%" : `${position}px`;

  return (
    <div
      style={{
        position: "absolute",
        left: `${(100 - lineWidth) / 2}%`,
        top: topVal,
        width: `${lineWidth}%`,
        height: thickness,
        borderRadius: thickness / 2,
        background: `linear-gradient(90deg, transparent 0%, ${color}60 20%, ${color} 50%, ${color}60 80%, transparent 100%)`,
        opacity: exitOpacity,
        zIndex: 35,
        overflow: "hidden",
      }}
    >
      {/* Shimmer */}
      <div style={{
        position: "absolute",
        top: -2, bottom: -2,
        left: `${shimmerX}%`,
        width: "20%",
        background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)`,
      }} />
    </div>
  );
};
