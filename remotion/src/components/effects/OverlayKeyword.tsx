import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

/**
 * OverlayKeyword — Large word placed over the talking-head at chest level.
 *
 * Designed to layer ON TOP of the avatar video for emphasis keywords.
 * Optional animated red strikethrough for negation moments.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const OverlayKeyword: React.FC<{
  text: string;
  durationInFrames: number;
  color?: string;
  fontSize?: number;
  fontWeight?: number;
  position?: "center" | "center-top" | "center-bottom";
  withStrikethrough?: boolean;
  strikethroughColor?: string;
  strikethroughDelay?: number;
  shadowStrength?: "none" | "subtle" | "strong";
}> = ({
  text,
  durationInFrames,
  color = "#FFFFFF",
  fontSize = 72,
  fontWeight = 900,
  position = "center",
  withStrikethrough = false,
  strikethroughColor = "#DC2626",
  strikethroughDelay = 10,
  shadowStrength = "strong",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entry: spring scale pop ──
  const s = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 250, mass: 0.6 },
  });

  const entryScale = interpolate(s, [0, 1], [0.9, 1.0]);
  const entryOpacity = interpolate(frame, [0, 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit: hard cut (1 frame) ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 1, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Strikethrough animation ──
  const strikethroughProgress = withStrikethrough
    ? interpolate(
        frame,
        [strikethroughDelay, strikethroughDelay + 10],
        [0, 100],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
      )
    : 0;

  // ── Position mapping ──
  const justifyContent =
    position === "center-top"
      ? "flex-start"
      : position === "center-bottom"
        ? "flex-end"
        : "center";

  const paddingTop = position === "center-top" ? 280 : 0;
  const paddingBottom = position === "center-bottom" ? 400 : 0;

  // ── Shadow ──
  const textShadow =
    shadowStrength === "none"
      ? "none"
      : shadowStrength === "strong"
        ? "0 4px 20px rgba(0,0,0,0.8), 0 2px 8px rgba(0,0,0,0.6)"
        : "0 2px 10px rgba(0,0,0,0.5)";

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent,
        paddingTop,
        paddingBottom,
        pointerEvents: "none",
        zIndex: 50,
        opacity: entryOpacity * exitOpacity,
      }}
    >
      <div
        style={{
          position: "relative",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${entryScale})`,
        }}
      >
        {/* Keyword text */}
        <span
          style={{
            fontSize,
            fontWeight,
            color,
            fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
            textAlign: "center",
            letterSpacing: -1,
            textShadow,
            textTransform: "uppercase",
          }}
        >
          {text}
        </span>

        {/* Strikethrough line */}
        {withStrikethrough && frame >= strikethroughDelay && (
          <div
            style={{
              position: "absolute",
              left: -8,
              right: -8,
              top: "50%",
              height: Math.max(4, fontSize * 0.04),
              backgroundColor: strikethroughColor,
              borderRadius: 3,
              transform: "translateY(-50%)",
              clipPath: `inset(0 ${100 - strikethroughProgress}% 0 0)`,
            }}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};
