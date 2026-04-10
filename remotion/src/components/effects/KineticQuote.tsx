import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * KineticQuote — Large dramatic text with word-by-word kinetic entrance.
 * Each word springs in from below with stagger. Optional quotation marks.
 * Used for powerful statements, hooks, or key messages.
 */
export const KineticQuote: React.FC<{
  text: string;
  color?: string;
  size?: number;
  staggerFrames?: number;
  showQuotes?: boolean;
  accentWords?: string[];
  accentColor?: string;
  durationInFrames: number;
}> = ({
  text,
  color = "#FFFFFF",
  size = 64,
  staggerFrames = 3,
  showQuotes = false,
  accentWords = [],
  accentColor = "#00E5FF",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");
  const accentSet = new Set(accentWords.map((w) => w.toLowerCase()));

  const exitOpacity = interpolate(frame, [durationInFrames - 5, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 48, right: 48,
        top: "50%",
        transform: "translateY(-50%)",
        textAlign: "center",
        zIndex: 40,
        opacity: exitOpacity,
      }}
    >
      {showQuotes && (
        <span style={{
          fontSize: size * 1.5,
          color: accentColor,
          opacity: 0.3,
          fontWeight: 900,
          lineHeight: 0.5,
          display: "block",
          marginBottom: 10,
          fontFamily: "Georgia, serif",
        }}>"</span>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8 }}>
        {words.map((word, i) => {
          const delay = i * staggerFrames;
          const localFrame = Math.max(0, frame - delay);
          const s = spring({ frame: localFrame, fps, config: { damping: 12, stiffness: 160 } });

          const isAccent = accentSet.has(word.toLowerCase().replace(/[^a-z0-9]/g, ""));

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                fontSize: size,
                fontWeight: isAccent ? 900 : 700,
                color: isAccent ? accentColor : color,
                fontFamily: "'Inter', 'Segoe UI', sans-serif",
                letterSpacing: "-0.03em",
                lineHeight: 1.2,
                transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)`,
                opacity: s,
                textShadow: isAccent
                  ? `0 0 20px ${accentColor}40`
                  : "0 4px 16px rgba(0,0,0,0.4)",
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
