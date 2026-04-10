import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * SceneBreak — GPU-safe transition overlay. Zero CSS filters.
 * Uses only opacity + transform + linear-gradient (all compositor-layer).
 */
export const SceneBreak: React.FC<{
  direction?: "left" | "right" | "center" | "whip-left" | "whip-right" | "iris-pulse";
}> = ({ direction = "whip-left" }) => {
  const frame = useCurrentFrame();

  const style = direction === "left" ? "whip-left"
    : direction === "right" ? "whip-right"
    : direction === "center" ? "iris-pulse"
    : direction;

  if (style === "iris-pulse") {
    const progress = interpolate(frame, [0, 10], [0, 1], {
      extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
    });
    const ringScale = interpolate(progress, [0, 1], [0.1, 2.5]);
    const ringOpacity = interpolate(progress, [0, 0.2, 0.6, 1], [0, 0.4, 0.2, 0]);
    const flashOpacity = interpolate(frame, [0, 2, 5, 10], [0, 0.12, 0.05, 0], {
      extrapolateRight: "clamp",
    });

    return (
      <AbsoluteFill style={{ zIndex: 50, pointerEvents: "none" }}>
        <div style={{
          position: "absolute", inset: 0,
          background: `radial-gradient(circle at 50% 50%, rgba(0, 229, 255, ${flashOpacity}), transparent 70%)`,
        }} />
        <div style={{
          position: "absolute",
          top: "50%", left: "50%",
          width: 800, height: 800,
          marginLeft: -400, marginTop: -400,
          borderRadius: "50%",
          border: `2px solid rgba(0, 229, 255, ${ringOpacity})`,
          transform: `scale(${ringScale})`,
        }} />
      </AbsoluteFill>
    );
  }

  // Whip-pan: a single gradient div moving across — no blur at all
  const isLeft = style === "whip-left";
  const progress = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.bezier(0.22, 1, 0.36, 1),
  });

  const startX = isLeft ? -260 : 1080;
  const endX = isLeft ? 1080 : -260;
  const streakX = interpolate(progress, [0, 1], [startX, endX]);
  const streakOpacity = interpolate(progress, [0, 0.2, 0.5, 0.8, 1], [0, 0.5, 0.7, 0.4, 0]);
  const ambientFlash = interpolate(progress, [0, 0.3, 0.6, 1], [0, 0.05, 0.03, 0]);

  return (
    <AbsoluteFill style={{ zIndex: 50, pointerEvents: "none" }}>
      {/* Full-screen ambient tint — opacity only */}
      <div style={{
        position: "absolute", inset: 0,
        background: `rgba(0, 229, 255, ${ambientFlash})`,
      }} />
      {/* Streak — gradient only, zero filter */}
      <div style={{
        position: "absolute",
        top: 0, bottom: 0,
        left: streakX,
        width: 260,
        opacity: streakOpacity,
        background: isLeft
          ? "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 40%, rgba(0,229,255,0.4) 60%, rgba(255,255,255,0.15) 80%, transparent 100%)"
          : "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 20%, rgba(0,229,255,0.4) 40%, rgba(255,255,255,0.3) 60%, transparent 100%)",
      }} />
    </AbsoluteFill>
  );
};
