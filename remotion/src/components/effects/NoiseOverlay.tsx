import React from "react";
import { AbsoluteFill, useCurrentFrame, random } from "remotion";

/**
 * NoiseOverlay — Subtle animated film grain / noise texture.
 * Adds premium cinema feel. Very lightweight — uses a small repeating SVG pattern.
 *
 * Props:
 * - opacity: grain visibility (0.02-0.08 is subtle, 0.1+ is noticeable)
 * - animated: whether grain pattern shifts each frame
 */
export const NoiseOverlay: React.FC<{
  opacity?: number;
  animated?: boolean;
}> = ({ opacity = 0.04, animated = true }) => {
  const frame = useCurrentFrame();

  // Shift the noise pattern slightly each frame for film-like grain
  const offsetX = animated ? Math.floor(random(`nx-${frame % 8}`) * 100) : 0;
  const offsetY = animated ? Math.floor(random(`ny-${frame % 8}`) * 100) : 0;

  // SVG noise pattern encoded as data URI — tiny and fast
  const noiseSvg = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E`;

  return (
    <AbsoluteFill
      style={{
        zIndex: 55,
        pointerEvents: "none",
        backgroundImage: `url("${noiseSvg}")`,
        backgroundPosition: `${offsetX}px ${offsetY}px`,
        backgroundSize: "200px 200px",
        opacity,
        mixBlendMode: "overlay",
      }}
    />
  );
};
