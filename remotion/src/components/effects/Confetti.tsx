import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

/**
 * Confetti — Celebration burst for proof/result/win moments.
 * Particles explode from center then drift down with rotation.
 */
export const Confetti: React.FC<{
  count?: number;
  colors?: string[];
  durationInFrames: number;
  originX?: number;
  originY?: number;
}> = ({
  count = 40,
  colors = ["#00E5FF", "#AB68FF", "#FFD700", "#FF6B6B", "#4ECDC4", "#FFFFFF"],
  durationInFrames,
  originX = 50,
  originY = 40,
}) => {
  const frame = useCurrentFrame();

  const pieces = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      angle: random(`ca-${i}`) * Math.PI * 2,
      speed: 3 + random(`cs-${i}`) * 8,
      rotSpeed: (random(`cr-${i}`) - 0.5) * 12,
      color: colors[Math.floor(random(`cc-${i}`) * colors.length)],
      width: 6 + random(`cw-${i}`) * 8,
      height: 4 + random(`ch-${i}`) * 6,
      gravity: 0.12 + random(`cg-${i}`) * 0.08,
      drag: 0.96 + random(`cd-${i}`) * 0.03,
    }));
  }, [count, colors]);

  return (
    <AbsoluteFill style={{ zIndex: 47, pointerEvents: "none", overflow: "hidden" }}>
      {pieces.map((p, i) => {
        // Physics: initial velocity decays, gravity pulls down
        let vx = Math.cos(p.angle) * p.speed;
        let vy = Math.sin(p.angle) * p.speed - 3; // bias upward
        let x = originX;
        let y = originY;

        // Simple euler integration
        for (let f = 0; f < frame; f++) {
          x += vx * 0.3;
          y += vy * 0.3;
          vx *= p.drag;
          vy *= p.drag;
          vy += p.gravity * 0.3; // gravity
        }

        if (y > 110) return null;

        const rotation = frame * p.rotSpeed;
        const opacity = interpolate(frame, [0, 2, durationInFrames - 6, durationInFrames], [0, 1, 0.6, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: p.width,
              height: p.height,
              background: p.color,
              borderRadius: 2,
              transform: `rotate(${rotation}deg)`,
              opacity,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
