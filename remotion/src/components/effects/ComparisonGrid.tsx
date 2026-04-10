import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
} from "remotion";

/**
 * ComparisonGrid — Side-by-side screenshot layout with optional VS divider.
 *
 * Used in editorial-authority style for comparison beats.
 * Each half holds a screenshot, with labels below and a VS badge between.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const ComparisonGrid: React.FC<{
  leftImage: string;
  rightImage: string;
  leftLabel?: string;
  rightLabel?: string;
  dividerType?: "vs" | "line" | "none";
  durationInFrames: number;
  backgroundColor?: string;
  labelColor?: string;
  vsColor?: string;
  vsBgColor?: string;
}> = ({
  leftImage,
  rightImage,
  leftLabel,
  rightLabel,
  dividerType = "vs",
  durationInFrames,
  backgroundColor = "#FFFFFF",
  labelColor = "#1A1A1A",
  vsColor = "#FFFFFF",
  vsBgColor = "#DC2626",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entry: both sides scale in ──
  const entryProgress = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 200 },
  });

  const entryScale = interpolate(entryProgress, [0, 1], [0.95, 1.0]);
  const entryOpacity = interpolate(frame, [0, 3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit: hard cut ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 1, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── VS badge pop ──
  const vsScale =
    dividerType === "vs"
      ? interpolate(
          spring({
            frame: Math.max(0, frame - 4),
            fps,
            config: { damping: 10, stiffness: 250, mass: 0.5 },
          }),
          [0, 1],
          [0.5, 1.0],
        )
      : 1;

  const vsOpacity =
    dividerType === "vs"
      ? interpolate(frame, [4, 7], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : 1;

  const imageStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    borderRadius: 12,
  };

  const halfStyle: React.CSSProperties = {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 16,
    padding: "0 16px",
    transform: `scale(${entryScale})`,
  };

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "center",
        padding: "120px 24px",
        gap: 0,
        opacity: entryOpacity * exitOpacity,
      }}
    >
      {/* Left side */}
      <div style={halfStyle}>
        <div
          style={{
            width: "100%",
            flex: 1,
            borderRadius: 12,
            overflow: "hidden",
            boxShadow: "0 4px 24px rgba(0,0,0,0.1)",
          }}
        >
          <Img src={staticFile(leftImage)} style={imageStyle} />
        </div>
        {leftLabel && (
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: labelColor,
              fontFamily: "'Inter', system-ui, sans-serif",
              textAlign: "center",
            }}
          >
            {leftLabel}
          </span>
        )}
      </div>

      {/* Divider */}
      {dividerType === "vs" && (
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: "50%",
            backgroundColor: vsBgColor,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 10,
            marginLeft: -20,
            marginRight: -20,
            transform: `scale(${vsScale})`,
            opacity: vsOpacity,
            boxShadow: "0 4px 16px rgba(0,0,0,0.2)",
          }}
        >
          <span
            style={{
              fontSize: 24,
              fontWeight: 900,
              color: vsColor,
              fontFamily: "'Inter', system-ui, sans-serif",
            }}
          >
            VS
          </span>
        </div>
      )}
      {dividerType === "line" && (
        <div
          style={{
            width: 2,
            height: "60%",
            backgroundColor: "rgba(0,0,0,0.15)",
            marginLeft: 8,
            marginRight: 8,
          }}
        />
      )}

      {/* Right side */}
      <div style={halfStyle}>
        <div
          style={{
            width: "100%",
            flex: 1,
            borderRadius: 12,
            overflow: "hidden",
            boxShadow: "0 4px 24px rgba(0,0,0,0.1)",
          }}
        >
          <Img src={staticFile(rightImage)} style={imageStyle} />
        </div>
        {rightLabel && (
          <span
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: labelColor,
              fontFamily: "'Inter', system-ui, sans-serif",
              textAlign: "center",
            }}
          >
            {rightLabel}
          </span>
        )}
      </div>
    </AbsoluteFill>
  );
};
