import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";

/**
 * NumberCounter — Animated number that counts up with optional suffix.
 * Perfect for stats, facts, "dozens of codes", engagement numbers.
 *
 * Props:
 * - from/to: count range
 * - suffix: text after the number ("+", "K", "%", etc.)
 * - prefix: text before the number ("$", "#", etc.)
 * - label: description text below
 * - color: number color
 * - size: font size
 */
export const NumberCounter: React.FC<{
  from?: number;
  to: number;
  suffix?: string;
  prefix?: string;
  label?: string;
  color?: string;
  size?: number;
  durationInFrames: number;
}> = ({
  from = 0,
  to,
  suffix = "",
  prefix = "",
  label,
  color = "#00E5FF",
  size = 120,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Count animation — fast start, decelerating end
  const countProgress = interpolate(frame, [0, durationInFrames * 0.6], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  const currentValue = Math.round(from + (to - from) * countProgress);

  // Scale pop when reaching target
  const atTarget = countProgress >= 0.99;
  const popScale = atTarget
    ? interpolate(frame - durationInFrames * 0.6, [0, 3, 6], [1.0, 1.08, 1.0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 1;

  // Entry animation
  const enter = spring({ frame, fps, config: { damping: 14, stiffness: 180 } });

  // Exit fade
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: enter * exitOpacity,
        transform: `translateY(${interpolate(enter, [0, 1], [30, 0])}px) scale(${popScale})`,
      }}
    >
      <div
        style={{
          fontSize: size,
          fontWeight: 900,
          fontFamily: "'Inter', 'Segoe UI', sans-serif",
          color,
          letterSpacing: "-0.03em",
          lineHeight: 1,
          textShadow: `0 0 30px ${color}40, 0 4px 20px rgba(0,0,0,0.5)`,
        }}
      >
        {prefix}{currentValue}{suffix}
      </div>
      {label && (
        <div
          style={{
            fontSize: 32,
            fontWeight: 600,
            color: "rgba(255, 255, 255, 0.7)",
            marginTop: 12,
            letterSpacing: "0.02em",
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};
