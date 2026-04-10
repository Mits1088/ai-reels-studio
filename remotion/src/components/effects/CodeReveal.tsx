import React from "react";
import { useCurrentFrame, interpolate, random } from "remotion";

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";

export const CodeReveal: React.FC<{
  text: string;
  startFrame: number;
  color?: string;
}> = ({ text, startFrame, color = "#00E5FF" }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  if (localFrame < 0) return null;

  const revealDuration = 20;
  const charsPerFrame = text.length / revealDuration;

  return (
    <div
      style={{
        position: "absolute",
        top: 80, left: 0, right: 0,
        display: "flex",
        justifyContent: "center",
        zIndex: 40,
      }}
    >
      <div
        style={{
          background: "rgba(0, 0, 0, 0.7)",
          backdropFilter: "blur(12px)",
          borderRadius: 16,
          padding: "16px 36px",
          border: `1px solid ${color}40`,
          boxShadow: `0 0 30px ${color}20, inset 0 0 20px ${color}08`,
        }}
      >
        <span
          style={{
            fontSize: 52,
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
            fontWeight: 700,
            letterSpacing: "0.05em",
          }}
        >
          {text.split("").map((char, i) => {
            const charRevealFrame = i / charsPerFrame;
            const isRevealed = localFrame > charRevealFrame;
            const isScrambling = localFrame > charRevealFrame - 8 && !isRevealed;

            let displayChar = " ";
            if (isRevealed) {
              displayChar = char;
            } else if (isScrambling) {
              const glyphIdx = Math.floor(random(`sc-${i}-${Math.floor(localFrame)}`) * GLYPHS.length);
              displayChar = GLYPHS[glyphIdx];
            }

            const charOpacity = isRevealed ? 1 : isScrambling ? 0.4 : 0;
            const charScale = isRevealed
              ? interpolate(localFrame - charRevealFrame, [0, 3], [1.3, 1.0], { extrapolateRight: "clamp" })
              : 1;

            return (
              <span
                key={i}
                style={{
                  color: isRevealed ? color : "#666",
                  opacity: charOpacity,
                  display: "inline-block",
                  transform: `scale(${charScale})`,
                  textShadow: isRevealed ? `0 0 16px ${color}80` : "none",
                  transition: "none",
                }}
              >
                {displayChar}
              </span>
            );
          })}
        </span>
      </div>
    </div>
  );
};
