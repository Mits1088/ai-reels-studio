import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * HighlightBox — Animated rectangle that highlights a region of the screen.
 * Use during demo sections to draw attention to a specific UI element.
 *
 * Coordinates are percentages of the composition (0-100).
 * The box draws itself on with a border animation, holds, then fades out.
 */
export const HighlightBox: React.FC<{
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  borderWidth?: number;
  borderRadius?: number;
  label?: string;
  labelPosition?: "top" | "bottom" | "left" | "right";
  durationInFrames: number;
}> = ({
  x,
  y,
  width,
  height,
  color = "#FF3B30",
  borderWidth = 3,
  borderRadius = 8,
  label,
  labelPosition = "top",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Draw-in: border scales from center
  const drawIn = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 180 },
  });

  // Fade out in last 8 frames
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Subtle pulse on the border (breathing effect)
  const pulse = interpolate(
    frame,
    [0, durationInFrames],
    [0, Math.PI * 4],
    { extrapolateRight: "clamp" }
  );
  const pulseOpacity = 0.7 + 0.3 * Math.sin(pulse);

  // Label entrance (staggered after box)
  const labelEnter = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: { damping: 20, stiffness: 160 },
  });

  const labelStyles: Record<string, React.CSSProperties> = {
    top: {
      bottom: "100%",
      left: "50%",
      transform: `translateX(-50%) translateY(${interpolate(labelEnter, [0, 1], [8, -6])}px)`,
    },
    bottom: {
      top: "100%",
      left: "50%",
      transform: `translateX(-50%) translateY(${interpolate(labelEnter, [0, 1], [-8, 6])}px)`,
    },
    left: {
      right: "100%",
      top: "50%",
      transform: `translateY(-50%) translateX(${interpolate(labelEnter, [0, 1], [8, -8])}px)`,
    },
    right: {
      left: "100%",
      top: "50%",
      transform: `translateY(-50%) translateX(${interpolate(labelEnter, [0, 1], [-8, 8])}px)`,
    },
  };

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        width: `${width}%`,
        height: `${height}%`,
        opacity: fadeOut,
        zIndex: 40,
        pointerEvents: "none",
      }}
    >
      {/* Highlight border */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          border: `${borderWidth}px solid ${color}`,
          borderRadius,
          opacity: pulseOpacity * drawIn,
          transform: `scale(${interpolate(drawIn, [0, 1], [1.08, 1])})`,
          boxShadow: `0 0 12px ${color}40, inset 0 0 8px ${color}15`,
        }}
      />

      {/* Optional label */}
      {label && (
        <div
          style={{
            position: "absolute",
            ...labelStyles[labelPosition],
            opacity: labelEnter * fadeOut,
            whiteSpace: "nowrap",
          }}
        >
          <div
            style={{
              background: color,
              color: "#FFFFFF",
              fontSize: 16,
              fontWeight: 700,
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
              padding: "4px 12px",
              borderRadius: 6,
              letterSpacing: "0.02em",
            }}
          >
            {label}
          </div>
        </div>
      )}
    </div>
  );
};
