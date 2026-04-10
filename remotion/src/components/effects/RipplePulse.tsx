import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * RipplePulse — Expanding concentric rings from a point.
 * Used for emphasis on taps, clicks, reveals, or impact moments.
 *
 * Props:
 * - x, y: center position (percent)
 * - rings: number of concentric rings
 * - color: ring color
 * - maxRadius: maximum ring size (percent of screen)
 */
export const RipplePulse: React.FC<{
  x?: number;
  y?: number;
  rings?: number;
  color?: string;
  maxRadius?: number;
  durationInFrames: number;
}> = ({
  x = 50,
  y = 50,
  rings = 3,
  color = "rgba(0, 229, 255, 0.4)",
  maxRadius = 50,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ zIndex: 48, pointerEvents: "none" }}>
      {Array.from({ length: rings }, (_, i) => {
        const delay = i * 4; // stagger each ring
        const localFrame = frame - delay;
        if (localFrame < 0) return null;

        const progress = interpolate(localFrame, [0, durationInFrames - delay], [0, 1], {
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.cubic),
        });

        const radius = progress * maxRadius;
        const opacity = interpolate(progress, [0, 0.2, 0.7, 1], [0, 0.8, 0.3, 0]);
        const borderWidth = interpolate(progress, [0, 1], [3, 1]);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: `${radius * 2}%`,
              height: `${radius * 2}%`,
              marginLeft: `${-radius}%`,
              marginTop: `${-radius}%`,
              borderRadius: "50%",
              border: `${borderWidth}px solid ${color}`,
              opacity,
              boxShadow: `0 0 ${8 * (1 - progress)}px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
