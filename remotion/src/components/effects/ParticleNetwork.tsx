import React from "react";
import { AbsoluteFill, useCurrentFrame, random } from "remotion";

/**
 * ParticleNetwork — Connected nodes/dots with lines between nearby particles.
 * Tech-feel network visualization. More sophisticated than plain floating particles.
 *
 * Props:
 * - count: number of nodes
 * - color: node and line color
 * - connectionDistance: max distance (px) for lines between nodes
 * - speed: movement speed
 */
export const ParticleNetwork: React.FC<{
  count?: number;
  color?: string;
  connectionDistance?: number;
  speed?: number;
}> = ({
  count = 20,
  color = "rgba(0, 229, 255, 0.4)",
  connectionDistance = 200,
  speed = 0.4,
}) => {
  const frame = useCurrentFrame();

  const nodes = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      baseX: random(`nx-${i}`) * 1080,
      baseY: random(`ny-${i}`) * 1920,
      vx: (random(`nvx-${i}`) - 0.5) * speed,
      vy: (random(`nvy-${i}`) - 0.5) * speed,
      size: 2 + random(`ns-${i}`) * 3,
      phase: random(`np-${i}`) * Math.PI * 2,
    }));
  }, [count, speed]);

  // Compute current positions
  const positions = nodes.map((n) => ({
    x: n.baseX + Math.sin(frame * 0.015 + n.phase) * 60 + n.vx * frame,
    y: n.baseY + Math.cos(frame * 0.012 + n.phase) * 40 + n.vy * frame,
    size: n.size,
  }));

  // Wrap positions to stay on screen
  positions.forEach((p) => {
    p.x = ((p.x % 1200) + 1200) % 1200 - 60;
    p.y = ((p.y % 2040) + 2040) % 2040 - 60;
  });

  // Find connections
  const lines: Array<{ x1: number; y1: number; x2: number; y2: number; opacity: number }> = [];
  for (let i = 0; i < positions.length; i++) {
    for (let j = i + 1; j < positions.length; j++) {
      const dx = positions[i].x - positions[j].x;
      const dy = positions[i].y - positions[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < connectionDistance) {
        lines.push({
          x1: positions[i].x,
          y1: positions[i].y,
          x2: positions[j].x,
          y2: positions[j].y,
          opacity: 1 - dist / connectionDistance,
        });
      }
    }
  }

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none" }}>
      <svg width="1080" height="1920" style={{ position: "absolute", top: 0, left: 0 }}>
        {/* Connection lines */}
        {lines.map((line, i) => (
          <line
            key={`l-${i}`}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke={color}
            strokeWidth={0.8}
            opacity={line.opacity * 0.3}
          />
        ))}
        {/* Nodes */}
        {positions.map((p, i) => (
          <circle
            key={`n-${i}`}
            cx={p.x}
            cy={p.y}
            r={p.size}
            fill={color}
            opacity={0.6}
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
