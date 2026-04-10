import React from "react";
import { useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * ShimmerBar — Animated progress/accent bar with a traveling shine effect.
 * Great for loading indicators, section dividers, or decorative accents.
 *
 * Props:
 * - width: bar width (percent of container)
 * - height: bar thickness
 * - color: bar color
 * - fillProgress: how full the bar is (0-1), animated
 * - position: "top" | "bottom" | "center"
 */
export const ShimmerBar: React.FC<{
  width?: number;
  height?: number;
  color?: string;
  fillProgress?: number;
  position?: "top" | "bottom" | "center";
  durationInFrames: number;
}> = ({
  width = 80,
  height = 4,
  color = "#00E5FF",
  fillProgress = 1,
  position = "center",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  // Animate fill
  const fill = interpolate(frame, [0, durationInFrames * 0.5], [0, fillProgress * 100], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Shimmer sweep position
  const shimmerX = interpolate(frame % 40, [0, 40], [-20, 120]);

  // Fade in/out
  const opacity = interpolate(frame, [0, 3, durationInFrames - 3, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const posStyle: React.CSSProperties =
    position === "top"
      ? { top: 80, left: `${(100 - width) / 2}%` }
      : position === "bottom"
      ? { bottom: 200, left: `${(100 - width) / 2}%` }
      : { top: "50%", left: `${(100 - width) / 2}%`, marginTop: -height / 2 };

  return (
    <div
      style={{
        position: "absolute",
        width: `${width}%`,
        height,
        borderRadius: height / 2,
        background: "rgba(255, 255, 255, 0.08)",
        overflow: "hidden",
        opacity,
        zIndex: 35,
        ...posStyle,
      }}
    >
      {/* Fill */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: `${fill}%`,
          background: `linear-gradient(90deg, ${color}80, ${color})`,
          borderRadius: height / 2,
          boxShadow: `0 0 12px ${color}40`,
        }}
      />
      {/* Shimmer shine */}
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: `${shimmerX}%`,
          width: "15%",
          background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)`,
        }}
      />
    </div>
  );
};
