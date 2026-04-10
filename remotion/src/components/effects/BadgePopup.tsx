import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * BadgePopup — Animated badge/tag that pops in with a bounce.
 * Used for labels like "NEW", "PRO TIP", "FREE", "HIDDEN", etc.
 */
export const BadgePopup: React.FC<{
  text: string;
  color?: string;
  textColor?: string;
  icon?: string;
  size?: "small" | "medium" | "large";
  durationInFrames: number;
}> = ({
  text,
  color = "#00E5FF",
  textColor = "#000000",
  icon,
  size = "medium",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, config: { damping: 10, stiffness: 200, mass: 0.7 } });
  const exitOpacity = interpolate(frame, [durationInFrames - 3, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const fontSize = size === "small" ? 18 : size === "large" ? 32 : 24;
  const padding = size === "small" ? "6px 14px" : size === "large" ? "14px 32px" : "10px 22px";

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        background: color,
        color: textColor,
        fontSize,
        fontWeight: 800,
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
        padding,
        borderRadius: 100,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        transform: `scale(${interpolate(s, [0, 1], [0, 1])})`,
        opacity: s * exitOpacity,
        boxShadow: `0 4px 20px ${color}40, 0 2px 8px rgba(0,0,0,0.3)`,
        zIndex: 55,
      }}
    >
      {icon && <span style={{ fontSize: fontSize * 1.1 }}>{icon}</span>}
      {text}
    </div>
  );
};
