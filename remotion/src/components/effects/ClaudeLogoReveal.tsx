import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, staticFile, Img } from "remotion";

/**
 * ClaudeLogoReveal — Claude logo slides down from above with spring curve,
 * orange radial glow pulses behind it on entry, then settles.
 * Designed for beat-01 of the "Things you didn't know" series.
 */
export const ClaudeLogoReveal: React.FC<{ durationInFrames: number }> = ({
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Spring slide-down from above — matches avatar isFromFullScreen spring (damping:18, stiffness:90)
  const slideIn = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 90 },
  });
  const translateY = interpolate(slideIn, [0, 1], [-320, 0]);

  // Fade in over first 8 frames
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Fade out in last 12 frames
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 12, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const finalOpacity = opacity * fadeOut;

  // Glow pulse: surges on entry then settles
  const glowOpacity = interpolate(
    frame,
    [0, 10, 22, 40, durationInFrames - 12, durationInFrames],
    [0, 0.0, 0.75, 0.45, 0.45, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        top: "16%",
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        zIndex: 25,
        opacity: finalOpacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {/* Orange glow radial gradient — behind logo */}
      <div
        style={{
          position: "absolute",
          width: 660,
          height: 260,
          borderRadius: 90,
          background: `radial-gradient(ellipse at center, rgba(232,119,34,${glowOpacity}) 0%, rgba(232,119,34,${glowOpacity * 0.3}) 40%, transparent 72%)`,
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
        }}
      />

      {/* Claude logo */}
      <Img
        src={staticFile("claude-logo.png")}
        style={{
          width: 480,
          height: "auto",
          position: "relative",
          zIndex: 1,
        }}
      />
    </div>
  );
};
