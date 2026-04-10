import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * ProgressDots — Step indicator showing progress through a sequence.
 * Shows which step you're on (e.g., "Step 2 of 4").
 * Common in tutorial/how-to reels.
 */
export const ProgressDots: React.FC<{
  total: number;
  current: number;
  color?: string;
  inactiveColor?: string;
  size?: number;
  durationInFrames: number;
}> = ({
  total,
  current,
  color = "#00E5FF",
  inactiveColor = "rgba(255, 255, 255, 0.15)",
  size = 10,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 200 } });
  const exitOpacity = interpolate(frame, [durationInFrames - 3, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "center",
        justifyContent: "center",
        opacity: enter * exitOpacity,
        transform: `translateY(${interpolate(enter, [0, 1], [10, 0])}px)`,
        zIndex: 55,
      }}
    >
      {Array.from({ length: total }, (_, i) => {
        const isActive = i < current;
        const isCurrent = i === current - 1;

        return (
          <div
            key={i}
            style={{
              width: isCurrent ? size * 3 : size,
              height: size,
              borderRadius: size / 2,
              background: isActive ? color : inactiveColor,
              boxShadow: isCurrent ? `0 0 10px ${color}60` : undefined,
              transition: "none",
            }}
          />
        );
      })}
    </div>
  );
};
