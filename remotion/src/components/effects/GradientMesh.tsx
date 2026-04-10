import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * GradientMesh — Smooth multi-blob gradient that morphs over time.
 * Premium ambient background. Cleaner than our rotating linear gradient.
 *
 * Props:
 * - colors: array of gradient blob colors
 * - speed: animation speed multiplier
 * - intensity: opacity of the blobs
 */
export const GradientMesh: React.FC<{
  colors?: string[];
  speed?: number;
  intensity?: number;
}> = ({
  colors = [
    "rgba(0, 229, 255, 0.12)",    // cyan
    "rgba(120, 80, 255, 0.10)",    // purple
    "rgba(0, 180, 220, 0.08)",     // teal
    "rgba(60, 0, 200, 0.06)",      // deep blue
  ],
  speed = 1,
  intensity = 1,
}) => {
  const frame = useCurrentFrame();
  const t = frame * 0.01 * speed;

  // 4 blobs that drift in elliptical paths
  const blobs = [
    {
      x: 50 + Math.sin(t * 0.7) * 25,
      y: 30 + Math.cos(t * 0.5) * 20,
      size: 50 + Math.sin(t * 0.3) * 10,
    },
    {
      x: 40 + Math.cos(t * 0.6) * 30,
      y: 65 + Math.sin(t * 0.8) * 15,
      size: 45 + Math.cos(t * 0.4) * 8,
    },
    {
      x: 70 + Math.sin(t * 0.9 + 2) * 20,
      y: 45 + Math.cos(t * 0.4 + 1) * 25,
      size: 40 + Math.sin(t * 0.5 + 3) * 12,
    },
    {
      x: 30 + Math.cos(t * 0.5 + 4) * 25,
      y: 80 + Math.sin(t * 0.7 + 2) * 15,
      size: 55 + Math.cos(t * 0.3 + 1) * 10,
    },
  ];

  return (
    <AbsoluteFill style={{ zIndex: 0 }}>
      {/* Dark base */}
      <div style={{ position: "absolute", inset: 0, background: "hsl(220, 30%, 6%)" }} />

      {/* Gradient blobs */}
      {blobs.map((blob, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${blob.x - blob.size / 2}%`,
            top: `${blob.y - blob.size / 2}%`,
            width: `${blob.size}%`,
            height: `${blob.size}%`,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${colors[i % colors.length]}, transparent 70%)`,
            opacity: intensity,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};
