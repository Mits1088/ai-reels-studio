import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

/**
 * TypewriterCode — Terminal-style code/command typing animation.
 * Characters appear one by one with a blinking cursor.
 * Perfect for showing prompts, commands, code snippets.
 */
export const TypewriterCode: React.FC<{
  text: string;
  prefix?: string;
  charsPerFrame?: number;
  color?: string;
  prefixColor?: string;
  size?: number;
  durationInFrames: number;
}> = ({
  text,
  prefix = "$ ",
  charsPerFrame = 0.8,
  color = "#00E5FF",
  prefixColor = "rgba(255, 255, 255, 0.4)",
  size = 36,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const charsVisible = Math.min(text.length, Math.floor(frame * charsPerFrame));
  const visibleText = text.slice(0, charsVisible);
  const isDone = charsVisible >= text.length;

  // Blinking cursor
  const cursorVisible = isDone ? Math.floor(frame * 0.06) % 2 === 0 : true;

  // Exit
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  // Enter
  const enterOpacity = interpolate(frame, [0, 3], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        opacity: enterOpacity * exitOpacity,
        zIndex: 40,
      }}
    >
      <div
        style={{
          background: "rgba(0, 0, 0, 0.75)",
          borderRadius: 14,
          padding: "14px 28px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.5)",
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
          fontSize: size,
          fontWeight: 500,
          letterSpacing: "0.02em",
          whiteSpace: "nowrap",
        }}
      >
        <span style={{ color: prefixColor }}>{prefix}</span>
        <span style={{ color }}>{visibleText}</span>
        <span style={{
          color,
          opacity: cursorVisible ? 1 : 0,
          fontWeight: 300,
        }}>▎</span>
      </div>
    </div>
  );
};
