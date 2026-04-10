import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
} from "remotion";

/**
 * EndScreen — YouTube end screen overlay (last 15-20s of video).
 * Shows two video recommendation cards and a subscribe circle.
 * Cards and subscribe element animate in with staggered springs.
 *
 * This is a visual overlay — it does NOT add interactive end screen elements
 * (those are added via YouTube Studio). It provides the visual treatment
 * so the end screen area has designed placeholders rather than raw video.
 */
export const EndScreen: React.FC<{
  leftTitle?: string;
  rightTitle?: string;
  leftThumbnail?: string;
  rightThumbnail?: string;
  channelAvatar?: string;
  channelName?: string;
  backgroundColor?: string;
  accentColor?: string;
  durationInFrames: number;
}> = ({
  leftTitle = "Watch Next",
  rightTitle = "Popular",
  leftThumbnail,
  rightThumbnail,
  channelAvatar,
  channelName,
  backgroundColor = "rgba(0, 0, 0, 0.85)",
  accentColor = "#FF0000",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Staggered entrances
  const bgEnter = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const leftCardEnter = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: { damping: 16, stiffness: 140 },
  });

  const rightCardEnter = spring({
    frame: Math.max(0, frame - 14),
    fps,
    config: { damping: 16, stiffness: 140 },
  });

  const subscribeEnter = spring({
    frame: Math.max(0, frame - 20),
    fps,
    config: { damping: 12, stiffness: 160 },
  });

  const cardStyle = (progress: number): React.CSSProperties => ({
    width: 360,
    height: 200,
    borderRadius: 16,
    overflow: "hidden",
    background: "rgba(255, 255, 255, 0.08)",
    border: "2px solid rgba(255, 255, 255, 0.12)",
    opacity: progress,
    transform: `scale(${interpolate(progress, [0, 1], [0.85, 1])}) translateY(${interpolate(progress, [0, 1], [20, 0])}px)`,
    display: "flex",
    flexDirection: "column" as const,
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 60,
        background: backgroundColor,
        opacity: bgEnter,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 40,
        pointerEvents: "none",
      }}
    >
      {/* Channel + subscribe row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          opacity: subscribeEnter,
          transform: `translateY(${interpolate(subscribeEnter, [0, 1], [15, 0])}px)`,
        }}
      >
        {/* Channel avatar */}
        {channelAvatar && (
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              overflow: "hidden",
              border: `2px solid ${accentColor}`,
            }}
          >
            <Img
              src={staticFile(channelAvatar)}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </div>
        )}

        {channelName && (
          <div
            style={{
              fontSize: 22,
              fontWeight: 600,
              color: "#FFFFFF",
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
            }}
          >
            {channelName}
          </div>
        )}

        {/* Subscribe pill */}
        <div
          style={{
            background: accentColor,
            borderRadius: 24,
            padding: "8px 24px",
            fontSize: 16,
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

      {/* Video recommendation cards */}
      <div
        style={{
          display: "flex",
          gap: 32,
          alignItems: "center",
        }}
      >
        {/* Left card */}
        <div style={cardStyle(leftCardEnter)}>
          {leftThumbnail ? (
            <Img
              src={staticFile(leftThumbnail)}
              style={{
                width: "100%",
                height: 140,
                objectFit: "cover",
              }}
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: 140,
                background: "rgba(255, 255, 255, 0.05)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="rgba(255,255,255,0.3)">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            </div>
          )}
          <div
            style={{
              padding: "10px 14px",
              fontSize: 14,
              fontWeight: 600,
              color: "#FFFFFF",
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
            }}
          >
            {leftTitle}
          </div>
        </div>

        {/* Right card */}
        <div style={cardStyle(rightCardEnter)}>
          {rightThumbnail ? (
            <Img
              src={staticFile(rightThumbnail)}
              style={{
                width: "100%",
                height: 140,
                objectFit: "cover",
              }}
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: 140,
                background: "rgba(255, 255, 255, 0.05)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="rgba(255,255,255,0.3)">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            </div>
          )}
          <div
            style={{
              padding: "10px 14px",
              fontSize: 14,
              fontWeight: 600,
              color: "#FFFFFF",
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
            }}
          >
            {rightTitle}
          </div>
        </div>
      </div>
    </div>
  );
};
