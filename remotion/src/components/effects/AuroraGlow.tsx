import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * AuroraGlow — Flowing aurora/northern lights effect.
 * Premium background for CTA moments, closing scenes, or high-energy beats.
 * Multiple translucent bands that flow and shift.
 */
export const AuroraGlow: React.FC<{
  colors?: string[];
  speed?: number;
  intensity?: number;
}> = ({
  colors = [
    "rgba(0, 229, 255, 0.12)",
    "rgba(120, 50, 255, 0.10)",
    "rgba(0, 255, 180, 0.08)",
    "rgba(80, 0, 220, 0.10)",
    "rgba(0, 180, 255, 0.06)",
  ],
  speed = 1,
  intensity = 1,
}) => {
  const frame = useCurrentFrame();
  const t = frame * 0.008 * speed;

  // 5 aurora bands — each flows at different speed and angle
  const bands = [
    { y: 25, width: 140, height: 30, angle: -8, speed: 1.0, drift: 0 },
    { y: 40, width: 120, height: 25, angle: 5, speed: 0.7, drift: 1 },
    { y: 55, width: 160, height: 20, angle: -3, speed: 1.3, drift: 2 },
    { y: 35, width: 100, height: 35, angle: 10, speed: 0.5, drift: 3 },
    { y: 60, width: 130, height: 22, angle: -6, speed: 0.9, drift: 4 },
  ];

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none", overflow: "hidden" }}>
      {bands.map((band, i) => {
        const xDrift = Math.sin(t * band.speed + band.drift) * 30;
        const yDrift = Math.cos(t * band.speed * 0.7 + band.drift) * 8;
        const scaleX = 1 + Math.sin(t * 0.5 + i) * 0.15;
        const opacity = (0.5 + Math.sin(t * band.speed * 0.8 + i * 1.5) * 0.3) * intensity;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${-20 + xDrift}%`,
              top: `${band.y + yDrift}%`,
              width: `${band.width}%`,
              height: `${band.height}%`,
              background: `linear-gradient(${band.angle + Math.sin(t + i) * 5}deg,
                transparent 0%,
                ${colors[i % colors.length]} 30%,
                ${colors[(i + 1) % colors.length]} 70%,
                transparent 100%)`,
              opacity,
              transform: `scaleX(${scaleX})`,
              borderRadius: "50%",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
