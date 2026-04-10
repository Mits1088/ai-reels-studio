import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, Img, staticFile } from "remotion";

/**
 * ComparisonSlider — Before/after comparison with animated sliding divider.
 * Perfect for showing transformations, results, or A/B comparisons.
 * The divider line slides from left to right revealing the "after" image.
 */
export const ComparisonSlider: React.FC<{
  beforeSrc: string;
  afterSrc: string;
  beforeLabel?: string;
  afterLabel?: string;
  dividerColor?: string;
  durationInFrames: number;
}> = ({
  beforeSrc,
  afterSrc,
  beforeLabel = "Before",
  afterLabel = "After",
  dividerColor = "#00E5FF",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Divider starts at 20% and sweeps to 80%
  const sweepProgress = interpolate(frame, [8, durationInFrames * 0.6], [0.2, 0.8], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.bezier(0.25, 0.1, 0.25, 1),
  });

  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 160 } });
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const dividerX = sweepProgress * 100;

  return (
    <div style={{
      width: "100%", height: "100%",
      opacity: enter * exitOpacity,
      transform: `scale(${interpolate(enter, [0, 1], [0.95, 1])})`,
      position: "relative",
      overflow: "hidden",
      borderRadius: 20,
    }}>
      {/* Before image (full) */}
      <Img src={staticFile(beforeSrc)} style={{
        position: "absolute", inset: 0,
        width: "100%", height: "100%",
        objectFit: "cover",
      }} />

      {/* After image (clipped) */}
      <div style={{
        position: "absolute", inset: 0,
        clipPath: `inset(0 0 0 ${dividerX}%)`,
      }}>
        <Img src={staticFile(afterSrc)} style={{
          width: "100%", height: "100%",
          objectFit: "cover",
        }} />
      </div>

      {/* Divider line */}
      <div style={{
        position: "absolute",
        top: 0, bottom: 0,
        left: `${dividerX}%`,
        width: 3,
        background: dividerColor,
        boxShadow: `0 0 12px ${dividerColor}60, 0 0 4px ${dividerColor}`,
        zIndex: 2,
      }}>
        {/* Handle circle */}
        <div style={{
          position: "absolute",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          width: 36, height: 36,
          borderRadius: "50%",
          background: dividerColor,
          boxShadow: `0 0 16px ${dividerColor}60`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          <span style={{ fontSize: 16, color: "#000", fontWeight: 900 }}>⟷</span>
        </div>
      </div>

      {/* Labels */}
      <div style={{
        position: "absolute", bottom: 16, left: 16,
        fontSize: 18, fontWeight: 700, color: "rgba(255,255,255,0.7)",
        background: "rgba(0,0,0,0.5)", borderRadius: 8, padding: "4px 12px",
        fontFamily: "'Inter', sans-serif",
      }}>{beforeLabel}</div>
      <div style={{
        position: "absolute", bottom: 16, right: 16,
        fontSize: 18, fontWeight: 700, color: "rgba(255,255,255,0.7)",
        background: "rgba(0,0,0,0.5)", borderRadius: 8, padding: "4px 12px",
        fontFamily: "'Inter', sans-serif",
      }}>{afterLabel}</div>
    </div>
  );
};
