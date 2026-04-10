import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

/**
 * NumberPopup — Large, centered, punchy number overlay.
 *
 * Two modes:
 * - Static: shows the number immediately (e.g. "6x", "8x")
 * - Counter: counts up from 0 to the target (e.g. $0 → $25B)
 *
 * Positioned center-screen in the upper area for maximum mobile visibility.
 * No background pill — just bold typography with strong shadow.
 */
export const NumberPopup: React.FC<{
  number: number | string;
  label?: string;
  suffix?: string;
  prefix?: string;
  durationInFrames: number;
  color?: string;
  textColor?: string;
  size?: "small" | "medium" | "large";
  position?: "top-left" | "top-right" | "top-center" | "center";
  counter?: boolean;
  counterDuration?: number;
}> = ({
  number,
  label,
  suffix = "",
  prefix = "",
  durationInFrames,
  color = "#4285F4",
  textColor = "#FFFFFF",
  size = "large",
  position = "center",
  counter = false,
  counterDuration = 18,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Spring pop-in
  const popIn = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 220, mass: 0.7 },
  });

  const scale = interpolate(popIn, [0, 1], [0.4, 1]);
  const slideY = interpolate(popIn, [0, 1], [30, 0]);

  // Fade out at end
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 6, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Counter animation
  const targetNum = typeof number === "number" ? number : parseFloat(String(number)) || 0;
  const counterProgress = interpolate(
    frame,
    [0, counterDuration],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  const displayNum = counter
    ? Math.round(targetNum * counterProgress)
    : number;

  // Sizing
  const fontSize = size === "large" ? 96 : size === "medium" ? 72 : 52;
  const suffixSize = Math.round(fontSize * 0.55);
  const labelSize = size === "large" ? 22 : size === "medium" ? 18 : 15;

  // Position — all variants centered horizontally, vertical varies
  const posStyle: React.CSSProperties = (() => {
    switch (position) {
      case "top-left":
        return { top: "12%", left: 60 };
      case "top-right":
        return { top: "12%", right: 60 };
      case "top-center":
        return { top: "12%", left: 0, right: 0, justifyContent: "center" };
      case "center":
      default:
        return { top: "22%", left: 0, right: 0, justifyContent: "center" };
    }
  })();

  return (
    <div
      style={{
        position: "absolute",
        ...posStyle,
        display: "flex",
        flexDirection: "column",
        alignItems: position === "top-left" ? "flex-start" : position === "top-right" ? "flex-end" : "center",
        opacity: fadeOut,
        transform: `translateY(${slideY}px) scale(${scale})`,
        zIndex: 50,
      }}
    >
      {/* Number row */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
        {prefix && (
          <span style={{
            fontSize: suffixSize,
            fontWeight: 800,
            color,
            fontFamily: "system-ui, -apple-system, sans-serif",
            textShadow: `0 0 30px ${color}88, 0 4px 12px rgba(0,0,0,0.4)`,
          }}>
            {prefix}
          </span>
        )}
        <span
          style={{
            fontSize,
            fontWeight: 900,
            color,
            lineHeight: 1,
            fontFamily: "system-ui, -apple-system, sans-serif",
            textShadow: `0 0 40px ${color}66, 0 4px 16px rgba(0,0,0,0.5)`,
            letterSpacing: -2,
          }}
        >
          {displayNum}
        </span>
        {suffix && (
          <span style={{
            fontSize: suffixSize,
            fontWeight: 800,
            color,
            fontFamily: "system-ui, -apple-system, sans-serif",
            textShadow: `0 0 30px ${color}88, 0 4px 12px rgba(0,0,0,0.4)`,
          }}>
            {suffix}
          </span>
        )}
      </div>

      {/* Label below */}
      {label && (
        <span
          style={{
            fontSize: labelSize,
            fontWeight: 700,
            color: textColor,
            opacity: 0.9,
            textTransform: "uppercase",
            letterSpacing: 3,
            fontFamily: "system-ui, -apple-system, sans-serif",
            marginTop: 8,
            textShadow: "0 2px 8px rgba(0,0,0,0.4)",
          }}
        >
          {label}
        </span>
      )}
    </div>
  );
};
