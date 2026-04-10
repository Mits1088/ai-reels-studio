import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * SubscribeCTA — Animated subscribe prompt for mid-video or end sections.
 * Shows a subscribe button with bell icon. Slides up, pulses, fades out.
 * Designed for YouTube landscape.
 */
export const SubscribeCTA: React.FC<{
  channelName?: string;
  position?: "bottom-center" | "bottom-right";
  accentColor?: string;
  durationInFrames: number;
}> = ({
  channelName,
  position = "bottom-center",
  accentColor = "#FF0000",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide up entrance
  const enter = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 140 },
  });

  // Bell wiggle at frame 20
  const bellWiggle = spring({
    frame: Math.max(0, frame - 20),
    fps,
    config: { damping: 6, stiffness: 300 },
  });
  const bellRotation = interpolate(bellWiggle, [0, 0.3, 0.6, 1], [0, 15, -10, 0]);

  // Exit
  const exit = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const slideY = interpolate(enter, [0, 1], [60, 0]) + exit * 60;
  const opacity = enter * (1 - exit);

  const posStyles: React.CSSProperties =
    position === "bottom-right"
      ? { bottom: 80, right: 60 }
      : { bottom: 80, left: "50%", transform: `translateX(-50%) translateY(${slideY}px)` };

  // Only apply translateY separately for bottom-right (not using translateX)
  const wrapperTransform =
    position === "bottom-right"
      ? `translateY(${slideY}px)`
      : `translateX(-50%) translateY(${slideY}px)`;

  return (
    <div
      style={{
        position: "absolute",
        ...(position === "bottom-right"
          ? { bottom: 80, right: 60 }
          : { bottom: 80, left: "50%" }),
        transform: wrapperTransform,
        zIndex: 50,
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 16,
        pointerEvents: "none",
      }}
    >
      {/* Subscribe button */}
      <div
        style={{
          background: accentColor,
          borderRadius: 8,
          padding: "12px 28px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          boxShadow: `0 4px 20px ${accentColor}60`,
        }}
      >
        {/* Bell icon */}
        <div style={{ transform: `rotate(${bellRotation}deg)` }}>
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="#FFFFFF"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </div>

        <div
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: "#FFFFFF",
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          Subscribe
        </div>
      </div>

      {/* Channel name (optional) */}
      {channelName && (
        <div
          style={{
            fontSize: 16,
            fontWeight: 500,
            color: "rgba(255, 255, 255, 0.7)",
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
          }}
        >
          {channelName}
        </div>
      )}
    </div>
  );
};
