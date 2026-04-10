import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * LinkOverlay — Displays a URL or link with an animated entrance.
 * Slides in from the right with an icon, holds, then slides out.
 * Designed for YouTube landscape — shows where to find the tool being discussed.
 */
export const LinkOverlay: React.FC<{
  url: string;
  label?: string;
  position?: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  accentColor?: string;
  durationInFrames: number;
}> = ({
  url,
  label,
  position = "bottom-right",
  accentColor = "#3B82F6",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide in
  const enter = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 160 },
  });

  // Slide out in last 10 frames
  const exit = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const slideX = interpolate(enter, [0, 1], [120, 0]) + exit * 120;
  const opacity = enter * (1 - exit);

  // Display text: label if provided, otherwise strip protocol from URL
  const displayText = label || url.replace(/^https?:\/\//, "").replace(/\/$/, "");

  const posStyles: Record<string, React.CSSProperties> = {
    "bottom-right": { bottom: 80, right: 40 },
    "bottom-left": { bottom: 80, left: 40 },
    "top-right": { top: 40, right: 40 },
    "top-left": { top: 40, left: 40 },
  };

  const isRight = position.includes("right");

  return (
    <div
      style={{
        position: "absolute",
        ...posStyles[position],
        zIndex: 45,
        opacity,
        transform: `translateX(${isRight ? slideX : -slideX}px)`,
        display: "flex",
        alignItems: "center",
        gap: 10,
        pointerEvents: "none",
      }}
    >
      {/* Accent bar */}
      <div
        style={{
          width: 4,
          height: 36,
          background: accentColor,
          borderRadius: 2,
          flexShrink: 0,
        }}
      />

      {/* Link card */}
      <div
        style={{
          background: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(8px)",
          borderRadius: 10,
          padding: "10px 20px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        {/* Link icon */}
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke={accentColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>

        <div>
          <div
            style={{
              fontSize: 18,
              fontWeight: 600,
              color: "#FFFFFF",
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
              letterSpacing: "-0.01em",
            }}
          >
            {displayText}
          </div>
        </div>
      </div>
    </div>
  );
};
