import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { fitText } from "@remotion/layout-utils";

/**
 * HeroTextCard — Large center-weighted text on a solid color background.
 *
 * Core component for the editorial-authority style.
 * Giant text fills the frame. Scale-pop-overshoot entry, static hold, instant exit.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const HeroTextCard: React.FC<{
  text: string;
  durationInFrames: number;
  backgroundColor?: string;
  textColor?: string;
  fontSize?: number;
  fontWeight?: number;
  withOvershoot?: boolean;
  shadowStrength?: "none" | "subtle" | "strong";
  /** Optional secondary line below the hero text */
  subtitle?: string;
  subtitleColor?: string;
  subtitleFontSize?: number;
  /** When true, ignores fontSize prop and auto-sizes text to fill 88% of frame width.
   *  Caps at 160px to avoid absurdly large single characters. */
  autoSize?: boolean;
}> = ({
  text,
  durationInFrames,
  backgroundColor = "#1A1A1A",
  textColor = "#FFFFFF",
  fontSize = 120,
  fontWeight = 900,
  withOvershoot = true,
  shadowStrength = "subtle",
  subtitle,
  subtitleColor,
  subtitleFontSize = 36,
  autoSize = false,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  // Auto-size: fit text to 88% of frame width, cap at 160px
  const resolvedFontSize = autoSize
    ? Math.min(
        160,
        fitText({
          text,
          fontFamily: "Inter",
          fontWeight: String(fontWeight),
          withinWidth: width * 0.88,
        }).fontSize
      )
    : fontSize;

  // ── Entry: scale-pop-overshoot ──
  const entryScale = withOvershoot
    ? interpolate(
        spring({
          frame,
          fps,
          config: { damping: 12, stiffness: 300, mass: 0.6 },
        }),
        [0, 1],
        [0.85, 1.0],
      )
    : interpolate(frame, [0, 3], [0.95, 1.0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });

  // ── Entry opacity (fast) ──
  const entryOpacity = interpolate(frame, [0, 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit: instant (1 frame) ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 1, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Subtitle stagger (appears slightly after hero) ──
  const subtitleOpacity = subtitle
    ? interpolate(frame, [4, 8], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  const subtitleY = subtitle
    ? interpolate(
        spring({
          frame: Math.max(0, frame - 4),
          fps,
          config: { damping: 18, stiffness: 200 },
        }),
        [0, 1],
        [20, 0],
      )
    : 0;

  // ── Shadow ──
  const textShadow =
    shadowStrength === "none"
      ? "none"
      : shadowStrength === "strong"
        ? "2px 4px 16px rgba(0,0,0,0.7)"
        : "2px 2px 8px rgba(0,0,0,0.5)";

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: entryOpacity * exitOpacity,
      }}
    >
      {/* Hero text */}
      <div
        style={{
          transform: `scale(${entryScale})`,
          fontSize: resolvedFontSize,
          fontWeight,
          color: textColor,
          fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
          textAlign: "center",
          lineHeight: 1.1,
          letterSpacing: -2,
          textShadow,
          padding: "0 48px",
          maxWidth: "90%",
          wordBreak: "break-word",
        }}
      >
        {text}
      </div>

      {/* Optional subtitle */}
      {subtitle && (
        <div
          style={{
            marginTop: 24,
            fontSize: subtitleFontSize,
            fontWeight: 500,
            color: subtitleColor || textColor,
            fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
            textAlign: "center",
            opacity: subtitleOpacity * exitOpacity,
            transform: `translateY(${subtitleY}px)`,
            textShadow: shadowStrength !== "none" ? "1px 1px 4px rgba(0,0,0,0.4)" : "none",
          }}
        >
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};
