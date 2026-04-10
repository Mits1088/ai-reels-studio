import React from "react";
import { useCurrentFrame } from "remotion";

/**
 * MorphBlob — Organic blob shape that continuously morphs.
 * Abstract premium visual — great as decorative background element
 * or behind text/cards for visual interest.
 */
export const MorphBlob: React.FC<{
  color?: string;
  size?: number;
  speed?: number;
  x?: number;
  y?: number;
}> = ({
  color = "rgba(0, 229, 255, 0.1)",
  size = 300,
  speed = 1,
  x = 50,
  y = 50,
}) => {
  const frame = useCurrentFrame();
  const t = frame * 0.02 * speed;

  // Generate morphing border-radius values
  const r1 = 30 + Math.sin(t) * 20;
  const r2 = 30 + Math.sin(t * 1.3 + 1) * 20;
  const r3 = 30 + Math.cos(t * 0.9 + 2) * 20;
  const r4 = 30 + Math.cos(t * 1.1 + 3) * 20;
  const r5 = 30 + Math.sin(t * 0.7 + 4) * 20;
  const r6 = 30 + Math.sin(t * 1.2 + 5) * 20;
  const r7 = 30 + Math.cos(t * 0.8 + 6) * 20;
  const r8 = 30 + Math.cos(t * 1.4 + 7) * 20;

  const borderRadius = `${r1}% ${r2}% ${r3}% ${r4}% / ${r5}% ${r6}% ${r7}% ${r8}%`;

  // Subtle rotation
  const rotation = Math.sin(t * 0.3) * 15;

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
        width: size,
        height: size,
        borderRadius,
        background: `radial-gradient(ellipse at 40% 40%, ${color}, ${color.replace(/[\d.]+\)$/, "0.02)")})`,
        zIndex: 1,
        pointerEvents: "none",
      }}
    />
  );
};
