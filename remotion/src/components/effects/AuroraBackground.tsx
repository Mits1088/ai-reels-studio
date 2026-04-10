import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * AuroraBackground — White base with soft pastel aurora blobs drifting slowly.
 * Inspired by Aceternity UI's aurora-background.
 * GPU-friendly: only transform + opacity, no blur filters.
 *
 * Designed as a clean, light background for demo/product scenes.
 */
export const AuroraBackground: React.FC<{
  speed?: number;
  intensity?: number;
  baseColor?: string;
  colors?: string[];
}> = ({
  speed = 1,
  intensity = 1,
  baseColor = "#FFFFFF",
  colors = [
    "rgba(120, 180, 255, 0.25)",   // soft blue
    "rgba(160, 120, 255, 0.20)",   // lavender
    "rgba(100, 220, 200, 0.18)",   // mint/teal
    "rgba(200, 140, 255, 0.15)",   // soft purple
    "rgba(80, 200, 255, 0.12)",    // sky blue
    "rgba(140, 255, 200, 0.10)",   // soft green
  ],
}) => {
  const frame = useCurrentFrame();
  const t = frame * 0.006 * speed;

  // 6 large soft blobs that drift in overlapping elliptical paths
  const blobs = [
    {
      x: 50 + Math.sin(t * 0.4) * 35,
      y: 25 + Math.cos(t * 0.3) * 20,
      w: 80 + Math.sin(t * 0.2) * 15,
      h: 50 + Math.cos(t * 0.25) * 10,
      rotation: Math.sin(t * 0.15) * 30,
    },
    {
      x: 30 + Math.cos(t * 0.35) * 30,
      y: 60 + Math.sin(t * 0.45) * 25,
      w: 70 + Math.cos(t * 0.3) * 12,
      h: 45 + Math.sin(t * 0.2) * 8,
      rotation: Math.cos(t * 0.2) * 25,
    },
    {
      x: 70 + Math.sin(t * 0.5 + 1.5) * 25,
      y: 40 + Math.cos(t * 0.35 + 0.8) * 30,
      w: 65 + Math.sin(t * 0.25 + 2) * 10,
      h: 55 + Math.cos(t * 0.3 + 1) * 12,
      rotation: Math.sin(t * 0.18 + 1) * 35,
    },
    {
      x: 45 + Math.cos(t * 0.3 + 3) * 30,
      y: 75 + Math.sin(t * 0.4 + 2) * 15,
      w: 75 + Math.cos(t * 0.2 + 1.5) * 10,
      h: 40 + Math.sin(t * 0.35 + 2) * 8,
      rotation: Math.cos(t * 0.12 + 2) * 20,
    },
    {
      x: 20 + Math.sin(t * 0.45 + 4) * 25,
      y: 15 + Math.cos(t * 0.3 + 3) * 20,
      w: 60 + Math.sin(t * 0.3 + 3) * 12,
      h: 35 + Math.cos(t * 0.2 + 2) * 8,
      rotation: Math.sin(t * 0.22 + 3) * 28,
    },
    {
      x: 80 + Math.cos(t * 0.25 + 5) * 20,
      y: 50 + Math.sin(t * 0.5 + 4) * 20,
      w: 55 + Math.cos(t * 0.35 + 4) * 10,
      h: 50 + Math.sin(t * 0.25 + 3) * 10,
      rotation: Math.cos(t * 0.17 + 4) * 30,
    },
  ];

  // Gentle fade-in
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ zIndex: 0, opacity: fadeIn }}>
      {/* White base */}
      <div style={{ position: "absolute", inset: 0, background: baseColor }} />

      {/* Aurora blobs */}
      {blobs.map((blob, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${blob.x - blob.w / 2}%`,
            top: `${blob.y - blob.h / 2}%`,
            width: `${blob.w}%`,
            height: `${blob.h}%`,
            borderRadius: "50%",
            background: `radial-gradient(ellipse at center, ${colors[i % colors.length]}, transparent 70%)`,
            opacity: intensity,
            transform: `rotate(${blob.rotation}deg)`,
          }}
        />
      ))}

      {/* Soft radial gradient overlay — brighter center, subtle edges */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 50% 40%, transparent 30%, rgba(255,255,255,0.6) 80%)",
        }}
      />
    </AbsoluteFill>
  );
};
