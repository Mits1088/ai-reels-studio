import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * ZoomParallax — Multi-layer parallax zoom effect.
 * Wraps children in layers that move at different speeds on zoom,
 * creating depth. Used for dramatic opening shots or transitions.
 *
 * Note: This is an overlay effect — renders semi-transparent shapes
 * at different parallax depths to create perceived 3D motion.
 */
export const ZoomParallax: React.FC<{
  layers?: number;
  color?: string;
  speed?: number;
  durationInFrames: number;
}> = ({
  layers = 4,
  color = "rgba(0, 229, 255, 0.04)",
  speed = 1,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: layers }, (_, i) => {
        const depth = (i + 1) / layers; // 0.25, 0.5, 0.75, 1.0
        const scale = 1 + progress * depth * 0.3 * speed;
        const opacity = interpolate(depth, [0, 1], [0.8, 0.2]);

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              inset: `-${20 * depth}%`,
              borderRadius: "50%",
              border: `1px solid ${color}`,
              transform: `scale(${scale})`,
              opacity: opacity * (1 - progress * 0.5),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
