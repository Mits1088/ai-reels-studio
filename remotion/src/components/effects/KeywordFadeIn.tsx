import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

/**
 * KeywordFadeIn — Words fade in one by one with staggered timing.
 *
 * Redesigned for center-screen visibility and punch.
 * Large text, strong shadow, no background pill.
 */
export const KeywordFadeIn: React.FC<{
  words: string;
  durationInFrames: number;
  delayPerWord?: number;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  position?: "center" | "top" | "bottom";
  yOffset?: number;
  withGlow?: boolean;
  glowColor?: string;
}> = ({
  words,
  durationInFrames,
  delayPerWord = 4,
  fontSize = 56,
  color = "#FFFFFF",
  fontWeight = 900,
  position = "center",
  yOffset = 0,
  withGlow = true,
  glowColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const wordList = words.split(" ");

  // Fade out at end
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 6, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // More centered vertical positions
  const topValue =
    position === "top" ? "18%" : position === "bottom" ? "70%" : "28%";

  const resolvedGlow = glowColor || color;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: topValue,
        transform: `translateY(${yOffset}px)`,
        display: "flex",
        justifyContent: "center",
        gap: fontSize * 0.3,
        flexWrap: "wrap",
        opacity: fadeOut,
        zIndex: 45,
        padding: "0 48px",
      }}
    >
      {wordList.map((word, i) => {
        const wordStart = i * delayPerWord;

        const wordProgress = spring({
          frame: Math.max(0, frame - wordStart),
          fps,
          config: { damping: 12, stiffness: 200, mass: 0.7 },
        });

        const wordOpacity = interpolate(wordProgress, [0, 1], [0, 1]);
        const wordScale = interpolate(wordProgress, [0, 1], [0.7, 1]);
        const wordY = interpolate(wordProgress, [0, 1], [15, 0]);

        return (
          <span
            key={`${word}-${i}`}
            style={{
              fontSize,
              fontWeight,
              color,
              fontFamily: "system-ui, -apple-system, sans-serif",
              opacity: wordOpacity,
              transform: `translateY(${wordY}px) scale(${wordScale})`,
              textShadow: withGlow
                ? `0 0 30px ${resolvedGlow}66, 0 0 60px ${resolvedGlow}33, 0 4px 12px rgba(0,0,0,0.5)`
                : "0 4px 12px rgba(0,0,0,0.5)",
              letterSpacing: -0.5,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
