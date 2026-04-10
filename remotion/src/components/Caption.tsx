import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * Caption — One word at a time, centered on screen.
 * Each word pops in cleanly. ALL-CAPS words get accent color.
 */
export const Caption: React.FC<{ text: string; durationInFrames: number }> = ({
  text,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");
  const framesPerWord = durationInFrames / words.length;

  // Which word is currently active
  const currentWordIndex = Math.min(
    Math.floor(frame / framesPerWord),
    words.length - 1
  );

  const word = words[currentWordIndex];
  const wordStart = currentWordIndex * framesPerWord;
  const localFrame = frame - wordStart;

  const isEmphasis = word === word.toUpperCase() && word.length > 1 && /[A-Z]/.test(word);

  // Pop in spring
  const s = spring({ frame: localFrame, fps, config: { damping: 18, stiffness: 280, mass: 0.6 } });

  // Container fade in/out
  const containerOpacity = interpolate(
    frame,
    [0, 3, durationInFrames - 4, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: 320,
        left: 48,
        right: 48,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 60,
        opacity: containerOpacity,
      }}
    >
      <div
        key={currentWordIndex}
        style={{
          background: "rgba(0, 0, 0, 0.72)",
          borderRadius: 16,
          padding: isEmphasis ? "12px 32px" : "10px 28px",
          border: isEmphasis
            ? "1px solid rgba(0, 229, 255, 0.25)"
            : "1px solid rgba(255, 255, 255, 0.06)",
          boxShadow: isEmphasis
            ? "0 0 24px rgba(0, 229, 255, 0.15), 0 4px 20px rgba(0,0,0,0.5)"
            : "0 4px 20px rgba(0,0,0,0.5)",
          transform: `scale(${interpolate(s, [0, 1], [0.85, 1.0])})`,
          opacity: s,
        }}
      >
        <span
          style={{
            fontSize: isEmphasis ? 62 : 54,
            fontWeight: isEmphasis ? 900 : 700,
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
            letterSpacing: isEmphasis ? "0.02em" : "-0.02em",
            color: isEmphasis ? "#00E5FF" : "#FFFFFF",
            textShadow: isEmphasis
              ? "0 0 20px rgba(0, 229, 255, 0.5)"
              : "0 2px 8px rgba(0,0,0,0.6)",
            whiteSpace: "nowrap",
          }}
        >
          {word}
        </span>
      </div>
    </div>
  );
};
