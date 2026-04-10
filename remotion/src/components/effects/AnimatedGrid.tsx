import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

/**
 * AnimatedGrid — Subtle dot grid background with traveling pulse waves.
 * Used for tech-feel backgrounds during list scenes, stats, or context beats.
 *
 * Props:
 * - cols/rows: grid density
 * - color: dot color
 * - pulseOrigin: where the pulse wave starts ({x: 0-1, y: 0-1})
 * - pulseSpeed: how fast the wave travels
 * - dotSize: base dot size
 */
export const AnimatedGrid: React.FC<{
  cols?: number;
  rows?: number;
  color?: string;
  pulseOrigin?: { x: number; y: number };
  pulseSpeed?: number;
  dotSize?: number;
  durationInFrames?: number;
}> = ({
  cols = 18,
  rows = 32,
  color = "rgba(0, 229, 255, 0.3)",
  pulseOrigin = { x: 0.5, y: 0.5 },
  pulseSpeed = 0.06,
  dotSize = 2,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const cellW = 1080 / cols;
  const cellH = 1920 / rows;

  // Pre-compute pulse ring position
  const pulseRadius = frame * pulseSpeed * Math.max(cols, rows);

  const dots = React.useMemo(() => {
    const d: Array<{ col: number; row: number; ox: number; oy: number }> = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        d.push({
          col: c,
          row: r,
          ox: (random(`gx-${c}-${r}`) - 0.5) * 4,
          oy: (random(`gy-${c}-${r}`) - 0.5) * 4,
        });
      }
    }
    return d;
  }, [cols, rows]);

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none" }}>
      {dots.map((dot, i) => {
        // Distance from pulse origin (in grid units)
        const dx = dot.col / cols - pulseOrigin.x;
        const dy = dot.row / rows - pulseOrigin.y;
        const dist = Math.sqrt(dx * dx + dy * dy) * Math.max(cols, rows);

        // Pulse wave — dots light up as the ring passes through
        const distFromPulse = Math.abs(dist - pulseRadius);
        const pulseGlow = distFromPulse < 3 ? interpolate(distFromPulse, [0, 3], [1, 0]) : 0;

        // Ambient breathing
        const breathe = 0.15 + Math.sin(frame * 0.03 + i * 0.1) * 0.08;

        const opacity = Math.min(1, breathe + pulseGlow * 0.7);
        const size = dotSize + pulseGlow * 2;

        const x = dot.col * cellW + cellW / 2 + dot.ox;
        const y = dot.row * cellH + cellH / 2 + dot.oy;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - size / 2,
              top: y - size / 2,
              width: size,
              height: size,
              borderRadius: "50%",
              background: color,
              opacity,
              boxShadow: pulseGlow > 0.3 ? `0 0 ${6 * pulseGlow}px ${color}` : undefined,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
