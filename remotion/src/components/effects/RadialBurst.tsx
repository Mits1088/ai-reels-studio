import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing, random } from "remotion";

/**
 * RadialBurst — Lines radiating from center for impact moments.
 * Quick burst that expands and fades — like a visual "boom".
 * Used at reveals, stat hits, or emphasis points.
 */
export const RadialBurst: React.FC<{
  x?: number;
  y?: number;
  lineCount?: number;
  color?: string;
  durationInFrames: number;
}> = ({
  x = 50,
  y = 50,
  lineCount = 16,
  color = "rgba(0, 229, 255, 0.5)",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });

  const opacity = interpolate(progress, [0, 0.15, 0.5, 1], [0, 0.8, 0.3, 0]);

  const lines = React.useMemo(() => {
    return Array.from({ length: lineCount }, (_, i) => ({
      angle: (360 / lineCount) * i + random(`rba-${i}`) * 8,
      length: 15 + random(`rbl-${i}`) * 25,
      width: 1 + random(`rbw-${i}`) * 2,
    }));
  }, [lineCount]);

  return (
    <AbsoluteFill style={{ zIndex: 47, pointerEvents: "none" }}>
      <div style={{
        position: "absolute",
        left: `${x}%`, top: `${y}%`,
        transform: "translate(-50%, -50%)",
      }}>
        {lines.map((line, i) => {
          const extendedLength = line.length * progress * 4;
          const startOffset = progress * line.length * 1.5;

          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: 0, top: 0,
                width: extendedLength,
                height: line.width,
                background: `linear-gradient(90deg, transparent, ${color})`,
                transformOrigin: "0 50%",
                transform: `rotate(${line.angle}deg) translateX(${startOffset}px)`,
                opacity,
                borderRadius: line.width / 2,
              }}
            />
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
