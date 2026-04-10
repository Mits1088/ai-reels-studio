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
 * ChapterDivider — Logo + wordmark centered on solid background.
 *
 * Used in editorial-authority style as a visual palate cleanser
 * between major sections. Gentle scale entrance, static hold, soft fade exit.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const ChapterDivider: React.FC<{
  title: string;
  durationInFrames: number;
  /** Path to logo image in remotion/public/ */
  logoSrc?: string;
  logoSize?: number;
  backgroundColor?: string;
  textColor?: string;
  fontSize?: number;
}> = ({
  title,
  durationInFrames,
  logoSrc,
  logoSize = 100,
  backgroundColor = "#FFFFFF",
  textColor = "#1A1A1A",
  fontSize = 32,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entry: opacity + scale ──
  const entryS = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 160 },
  });

  const entryScale = interpolate(entryS, [0, 1], [0.95, 1.0]);
  const entryOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit: soft fade ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 4, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Title stagger (appears after logo) ──
  const titleOpacity = interpolate(frame, [6, 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const titleY = interpolate(
    spring({
      frame: Math.max(0, frame - 6),
      fps,
      config: { damping: 18, stiffness: 180 },
    }),
    [0, 1],
    [12, 0],
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 24,
        opacity: entryOpacity * exitOpacity,
        transform: `scale(${entryScale})`,
      }}
    >
      {/* Logo */}
      {logoSrc && (
        <div
          style={{
            width: logoSize,
            height: logoSize,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Img
            src={staticFile(logoSrc)}
            style={{
              maxWidth: "100%",
              maxHeight: "100%",
              objectFit: "contain",
            }}
          />
        </div>
      )}

      {/* Title wordmark */}
      <div
        style={{
          fontSize,
          fontWeight: 600,
          color: textColor,
          fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
          textAlign: "center",
          letterSpacing: -0.5,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          padding: "0 48px",
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};
