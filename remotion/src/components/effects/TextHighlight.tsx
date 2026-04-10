import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";

/**
 * TextHighlight — Large statement text with an animated highlight sweep.
 * Used for key statements, quotes, stats, or emphasis text overlays.
 *
 * Props:
 * - text: the statement
 * - highlightWords: which words get the colored highlight sweep
 * - color: highlight color
 * - size: font size
 */
export const TextHighlight: React.FC<{
  text: string;
  highlightWords?: string[];
  color?: string;
  size?: number;
  durationInFrames: number;
}> = ({
  text,
  highlightWords = [],
  color = "#00E5FF",
  size = 56,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 180 } });
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  const highlightSet = new Set(highlightWords.map((w) => w.toLowerCase()));

  return (
    <div
      style={{
        position: "absolute",
        left: 48,
        right: 48,
        top: "50%",
        transform: `translateY(-50%) translateY(${interpolate(enter, [0, 1], [20, 0])}px)`,
        opacity: enter * exitOpacity,
        textAlign: "center",
        zIndex: 35,
      }}
    >
      <span
        style={{
          fontSize: size,
          fontWeight: 800,
          fontFamily: "'Inter', 'Segoe UI', sans-serif",
          lineHeight: 1.3,
          letterSpacing: "-0.02em",
        }}
      >
        {words.map((word, i) => {
          const isHighlighted = highlightSet.has(word.toLowerCase().replace(/[^a-z0-9]/g, ""));

          // Highlight sweep: a colored underline/bg that slides in
          const sweepDelay = i * 2;
          const sweepProgress = isHighlighted
            ? interpolate(frame, [sweepDelay + 4, sweepDelay + 8], [0, 100], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            : 0;

          return (
            <span
              key={i}
              style={{
                display: "inline",
                color: isHighlighted ? color : "#FFFFFF",
                fontWeight: isHighlighted ? 900 : 800,
                position: "relative",
                textShadow: isHighlighted
                  ? `0 0 20px ${color}40`
                  : "0 2px 8px rgba(0,0,0,0.5)",
              }}
            >
              {isHighlighted && (
                <span
                  style={{
                    position: "absolute",
                    bottom: -2,
                    left: 0,
                    width: `${sweepProgress}%`,
                    height: 4,
                    background: `linear-gradient(90deg, ${color}, ${color}80)`,
                    borderRadius: 2,
                    boxShadow: `0 0 8px ${color}40`,
                  }}
                />
              )}
              {word}{" "}
            </span>
          );
        })}
      </span>
    </div>
  );
};
