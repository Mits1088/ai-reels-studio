import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { AnimatedText as AnimatedTextBase } from "remotion-animate-text";

// Cast needed: package was compiled with React 17 JSX types; React 19 needs this bridge
const AnimatedText = AnimatedTextBase as unknown as React.FC<{
  duration: number;
  animation: object;
  hideLoading?: boolean;
  children: React.ReactNode;
}>;

/**
 * CharKeyword — Character-level text animation for single high-impact words.
 *
 * Powered by remotion-animate-text. Unlike KeywordFadeIn (word-level stagger),
 * this animates every individual character — creating explosive reveal energy
 * for short emotional keywords in hooks and proof beats.
 *
 * When to use CharKeyword vs KeywordFadeIn:
 *   - CharKeyword: single words or 2-word phrases that ARE the emphasis
 *     ("WRONG", "ZERO", "FREE", "GONE.", "6X FASTER")
 *   - KeywordFadeIn: multi-word reveals where word-level stagger reads cleanly
 *     ("No retraining.", "Works on any model.")
 *
 * Presets:
 *   - "explode"  — chars scatter-pop from 0.3 scale with rotation. Most dramatic.
 *   - "rise"     — chars lift up from below. Confident, upward energy.
 *   - "cascade"  — chars slide in left-to-right. Sequential, controlled.
 *
 * Frame-driven animation via remotion-animate-text's interpolate integration.
 */

type CharKeywordPreset = "explode" | "rise" | "cascade";

const PRESETS: Record<CharKeywordPreset, object> = {
  explode: {
    delimiter: "",       // character-level (empty = each char)
    opacity: [0, 1],
    scale: [0.3, 1],
    y: [30, 0],
    rotate: [15, 0],
  },
  rise: {
    delimiter: "",
    opacity: [0, 1],
    scale: [0.6, 1],
    y: [60, 0],
    rotate: [0, 0],
  },
  cascade: {
    delimiter: "",
    opacity: [0, 1],
    scale: [0.85, 1],
    y: [20, 0],
    x: [-30, 0],
  },
};

export const CharKeyword: React.FC<{
  /** The word or short phrase to animate. Keep under 10 chars for readability. */
  text: string;
  durationInFrames: number;
  /**
   * Animation preset. Default: "explode".
   * explode  = scatter-pop per character (most energetic, use for hook words)
   * rise     = lift up from below (confident, good for proof stats)
   * cascade  = left-to-right slide per character (controlled, good for names)
   */
  preset?: CharKeywordPreset;
  /**
   * Frames over which all characters animate in. Default: 40% of durationInFrames,
   * capped at 24 frames. Longer = slower stagger; shorter = faster pop-in.
   */
  animDuration?: number;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  /** Vertical anchor. Default: "center" (28% from top, above avatar head in split-screen). */
  position?: "top" | "center" | "bottom";
  /** Additional Y offset in pixels. */
  yOffset?: number;
}> = ({
  text,
  durationInFrames,
  preset = "explode",
  animDuration,
  fontSize = 120,
  color = "#FFFFFF",
  fontWeight = 900,
  position = "center",
  yOffset = 0,
}) => {
  const frame = useCurrentFrame();

  const resolvedAnimDuration =
    animDuration ?? Math.min(24, Math.floor(durationInFrames * 0.4));

  // Exit fade (last 6 frames)
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 6, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const topValue =
    position === "top"
      ? "18%"
      : position === "bottom"
        ? "70%"
        : "28%";

  return (
    <AbsoluteFill style={{ zIndex: 46, opacity: exitOpacity, pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: topValue,
          display: "flex",
          justifyContent: "center",
          padding: "0 48px",
          transform: `translateY(${yOffset}px)`,
        }}
      >
        <div
          style={{
            fontSize,
            fontWeight,
            color,
            fontFamily: "system-ui, -apple-system, sans-serif",
            letterSpacing: -2,
            textShadow: "0 4px 24px rgba(0,0,0,0.65)",
            textAlign: "center",
            lineHeight: 1,
          }}
        >
          <AnimatedText
            duration={resolvedAnimDuration}
            animation={PRESETS[preset]}
            hideLoading
          >
            {text}
          </AnimatedText>
        </div>
      </div>
    </AbsoluteFill>
  );
};
