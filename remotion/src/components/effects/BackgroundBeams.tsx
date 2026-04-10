import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * BackgroundBeams — Thin luminous beams sweeping across a white background.
 * Inspired by Aceternity UI's background-beams.
 * GPU-friendly: only transform + opacity on SVG paths.
 *
 * Clean, elegant, non-distracting. Perfect behind demo content.
 */
export const BackgroundBeams: React.FC<{
  beamCount?: number;
  color?: string;
  speed?: number;
  intensity?: number;
  baseColor?: string;
}> = ({
  beamCount = 12,
  color = "rgba(120, 160, 255, 0.15)",
  speed = 1,
  intensity = 1,
  baseColor = "#FFFFFF",
}) => {
  const frame = useCurrentFrame();
  const t = frame * 0.008 * speed;

  // Generate beam paths — thin curved lines sweeping from different origins
  const beams = Array.from({ length: beamCount }, (_, i) => {
    const seed = i * 1.7 + 0.5;
    const phase = seed * 2.1;

    // Origin point — beams radiate from edges
    const originSide = i % 4; // 0=top, 1=right, 2=bottom, 3=left
    let x1: number, y1: number;
    switch (originSide) {
      case 0: x1 = (i / beamCount) * 100; y1 = -5; break;
      case 1: x1 = 105; y1 = (i / beamCount) * 100; break;
      case 2: x1 = (1 - i / beamCount) * 100; y1 = 105; break;
      default: x1 = -5; y1 = (1 - i / beamCount) * 100; break;
    }

    // Control points drift over time
    const cx1 = 30 + Math.sin(t * 0.3 + phase) * 25;
    const cy1 = 30 + Math.cos(t * 0.4 + phase * 0.7) * 25;
    const cx2 = 70 + Math.cos(t * 0.35 + phase * 1.2) * 25;
    const cy2 = 70 + Math.sin(t * 0.25 + phase * 0.9) * 25;

    // End point — opposite side
    const x2 = 50 + Math.sin(t * 0.2 + seed) * 50;
    const y2 = 50 + Math.cos(t * 0.15 + seed * 1.3) * 50;

    // Each beam fades in and out on its own cycle
    const beamOpacity = interpolate(
      Math.sin(t * 0.5 + phase),
      [-1, -0.3, 0.3, 1],
      [0, 0.4, 0.8, 1],
    );

    const strokeWidth = 1 + Math.sin(t * 0.3 + seed * 2) * 0.5;

    return {
      path: `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`,
      opacity: beamOpacity * intensity,
      strokeWidth,
    };
  });

  // Gentle fade-in
  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ zIndex: 0, opacity: fadeIn }}>
      {/* White base */}
      <div style={{ position: "absolute", inset: 0, background: baseColor }} />

      {/* SVG beam layer */}
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
        }}
      >
        <defs>
          {/* Gradient for beam glow */}
          <linearGradient id="beam-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0" />
            <stop offset="30%" stopColor={color} stopOpacity="0.6" />
            <stop offset="70%" stopColor={color} stopOpacity="0.6" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        {beams.map((beam, i) => (
          <path
            key={i}
            d={beam.path}
            fill="none"
            stroke="url(#beam-grad)"
            strokeWidth={beam.strokeWidth}
            opacity={beam.opacity}
            strokeLinecap="round"
          />
        ))}
      </svg>

      {/* Subtle dot grid overlay for texture */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.03,
          backgroundImage:
            "radial-gradient(circle, rgba(0,0,0,0.3) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
    </AbsoluteFill>
  );
};
