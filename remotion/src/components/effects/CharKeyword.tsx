import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

type CharKeywordPreset = "explode" | "rise" | "cascade";

/**
 * CharKeyword — Character-level text animation for single high-impact words.
 *
 * Pure Remotion implementation (no external lib) — avoids the dual-React-version
 * crash that remotion-animate-text causes by bundling its own React in dist/.
 *
 * When to use CharKeyword vs KeywordFadeIn:
 *   - CharKeyword: single words or 2-word phrases that ARE the emphasis
 *     ("WRONG", "ZERO", "FREE", "GONE.", "6X FASTER")
 *   - KeywordFadeIn: multi-word reveals where word-level stagger reads cleanly
 *
 * Presets:
 *   - "explode"  — chars scatter-pop from 0.3 scale with rotation. Most dramatic.
 *   - "rise"     — chars lift up from below. Confident, upward energy.
 *   - "cascade"  — chars slide in left-to-right. Sequential, controlled.
 */

export const CharKeyword: React.FC<{
  text: string;
  durationInFrames: number;
  preset?: CharKeywordPreset;
  /** Frames for the full animation cycle. Default: 40% of durationInFrames, capped at 24. */
  animDuration?: number;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  /** Vertical anchor. Default: "center" (28% from top, above avatar in split-screen). */
  position?: "top" | "center" | "bottom";
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
  const { fps } = useVideoConfig();

  const chars = text.split("");
  const resolvedAnimDuration = animDuration ?? Math.min(24, Math.floor(durationInFrames * 0.4));
  const staggerPerChar = Math.max(1, Math.floor(resolvedAnimDuration / Math.max(1, chars.length)));

  const exitOpacity = interpolate(
    frame,
    [Math.max(0, durationInFrames - 6), durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const topValue =
    position === "top" ? "18%" : position === "bottom" ? "70%" : "28%";

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
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            textShadow: "0 4px 24px rgba(0,0,0,0.65)",
            lineHeight: 1,
          }}
        >
          {chars.map((char, i) => {
            const delay = i * staggerPerChar;
            const localFrame = Math.max(0, frame - delay);
            const sv = spring({
              frame: localFrame,
              fps,
              config: { damping: 12, stiffness: 280, mass: 0.6 },
            });

            let scale = 1;
            let opacity = 1;
            let translateY = 0;
            let rotate = 0;
            let translateX = 0;

            switch (preset) {
              case "explode":
                scale = interpolate(sv, [0, 1], [0.3, 1.0]);
                opacity = interpolate(sv, [0, 0.3, 1], [0, 1, 1]);
                translateY = interpolate(sv, [0, 1], [30, 0]);
                rotate = interpolate(sv, [0, 1], [15, 0]);
                break;
              case "rise":
                scale = interpolate(sv, [0, 1], [0.6, 1.0]);
                opacity = interpolate(sv, [0, 0.3, 1], [0, 1, 1]);
                translateY = interpolate(sv, [0, 1], [60, 0]);
                break;
              case "cascade":
                scale = interpolate(sv, [0, 1], [0.85, 1.0]);
                opacity = interpolate(sv, [0, 0.3, 1], [0, 1, 1]);
                translateY = interpolate(sv, [0, 1], [20, 0]);
                translateX = interpolate(sv, [0, 1], [-30, 0]);
                break;
            }

            return (
              <span
                key={i}
                style={{
                  fontSize,
                  fontWeight,
                  color,
                  fontFamily: "system-ui, -apple-system, sans-serif",
                  letterSpacing: -1,
                  display: "inline-block",
                  transform: `translate(${translateX}px, ${translateY}px) rotate(${rotate}deg) scale(${scale})`,
                  opacity,
                  whiteSpace: char === " " ? "pre" : "normal",
                }}
              >
                {char}
              </span>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
