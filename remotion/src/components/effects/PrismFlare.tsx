import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * PrismFlare — Rainbow/prismatic lens flare that sweeps across.
 * Subtle and premium — used at impact moments or reveals.
 * The flare travels diagonally with chromatic spread.
 */
export const PrismFlare: React.FC<{
  startFrame?: number;
  speed?: number;
  intensity?: number;
  angle?: number;
  durationInFrames: number;
}> = ({
  startFrame = 0,
  speed = 1,
  intensity = 0.5,
  angle = 30,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;
  if (localFrame < 0) return null;

  const progress = interpolate(localFrame, [0, durationInFrames * 0.8 / speed], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.bezier(0.25, 0.1, 0.25, 1),
  });

  const opacity = interpolate(progress, [0, 0.2, 0.5, 0.8, 1], [0, intensity, intensity * 0.7, intensity * 0.3, 0]);

  // Flare position moves diagonally
  const x = interpolate(progress, [0, 1], [-20, 120]);
  const y = interpolate(progress, [0, 1], [-10, 60]);

  return (
    <AbsoluteFill style={{ zIndex: 49, pointerEvents: "none" }}>
      {/* Main prismatic streak */}
      <div style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        width: 300,
        height: 8,
        transform: `rotate(${angle}deg)`,
        background: `linear-gradient(90deg,
          rgba(255, 0, 0, ${opacity * 0.3}),
          rgba(255, 150, 0, ${opacity * 0.3}),
          rgba(255, 255, 0, ${opacity * 0.25}),
          rgba(0, 255, 100, ${opacity * 0.25}),
          rgba(0, 200, 255, ${opacity * 0.3}),
          rgba(100, 0, 255, ${opacity * 0.3}),
          rgba(200, 0, 255, ${opacity * 0.2}))`,
      }} />
      {/* Soft halo around the flare */}
      <div style={{
        position: "absolute",
        left: `${x - 5}%`,
        top: `${y - 3}%`,
        width: 350,
        height: 80,
        transform: `rotate(${angle}deg)`,
        background: `radial-gradient(ellipse, rgba(255, 255, 255, ${opacity * 0.08}), transparent 60%)`,
      }} />
    </AbsoluteFill>
  );
};
