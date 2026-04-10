import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * GlassCard — Frosted glass card with subtle border glow.
 * Use for info overlays, stat displays, feature callouts.
 * Wraps any content with a premium glassmorphism container.
 */
export const GlassCard: React.FC<{
  children: React.ReactNode;
  width?: string;
  accentColor?: string;
  durationInFrames: number;
  enterFrom?: "bottom" | "left" | "right" | "scale";
}> = ({
  children,
  width = "85%",
  accentColor = "#00E5FF",
  durationInFrames,
  enterFrom = "bottom",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, config: { damping: 14, stiffness: 180 } });
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  let enterTransform = "";
  switch (enterFrom) {
    case "bottom": enterTransform = `translateY(${interpolate(s, [0, 1], [50, 0])}px)`; break;
    case "left": enterTransform = `translateX(${interpolate(s, [0, 1], [-80, 0])}px)`; break;
    case "right": enterTransform = `translateX(${interpolate(s, [0, 1], [80, 0])}px)`; break;
    case "scale": enterTransform = `scale(${interpolate(s, [0, 1], [0.85, 1])})`; break;
  }

  return (
    <div
      style={{
        width,
        margin: "0 auto",
        background: "rgba(255, 255, 255, 0.04)",
        backdropFilter: "blur(12px)",
        borderRadius: 20,
        border: "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: `0 8px 40px rgba(0, 0, 0, 0.4), 0 0 1px ${accentColor}20`,
        padding: "28px 32px",
        opacity: s * exitOpacity,
        transform: enterTransform,
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Top accent line */}
      <div style={{
        position: "absolute",
        top: 0, left: "20%", right: "20%",
        height: 1,
        background: `linear-gradient(90deg, transparent, ${accentColor}30, transparent)`,
      }} />
      {children}
    </div>
  );
};
