/**
 * TypingText — vendored from clippkit (MIT)
 * Source: https://github.com/reactvideoeditor/clippkit
 *         apps/docs/registry/default/components/typing-text.tsx
 *
 * Adapted for the AI Reels Studio pipeline:
 *  - Named export instead of default
 *  - Theme defaults
 *  - Wraps in AbsoluteFill for OVERLAY_REGISTRY use
 *  - Optional position prop (top / center / bottom)
 *
 * Use it to mock CLI / chat / prompt interactions where you want the viewer
 * to feel "Claude is typing right now". Pair with a translucent dark
 * background card for terminal-style mockups.
 */
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface TypingTextProps {
  text?: string;
  textColor?: string;
  cursorColor?: string;
  fontSize?: string;
  fontFamily?: string;
  fontWeight?: number | string;
  /** Total frames to type out the entire text. Default: 5 frames per character. */
  durationInFramesToType?: number;
  /** Frames per blink cycle. */
  cursorBlinkSpeed?: number;
  position?: "top" | "center" | "bottom";
  paddingY?: number;
  backgroundColor?: string;
  durationInFrames?: number;
}

export const TypingText: React.FC<TypingTextProps> = ({
  text = "TYPE ME...",
  textColor = "#FFFFFF",
  cursorColor = "#D97757",
  fontSize = "3rem",
  fontFamily = "'JetBrains Mono', 'Courier New', monospace",
  fontWeight = 600,
  durationInFramesToType,
  cursorBlinkSpeed = 15,
  position = "center",
  paddingY = 200,
  backgroundColor,
}) => {
  const frame = useCurrentFrame();

  const actualDuration =
    durationInFramesToType !== undefined
      ? durationInFramesToType
      : text.length * 5;

  const visibleCharacters = Math.floor(
    interpolate(frame, [0, actualDuration], [0, text.length], {
      extrapolateRight: "clamp",
    }),
  );

  const characters = text.slice(0, visibleCharacters);
  const showCursor = frame % cursorBlinkSpeed < cursorBlinkSpeed / 2;

  const justifyContent =
    position === "top"
      ? "flex-start"
      : position === "bottom"
        ? "flex-end"
        : "center";

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent,
        paddingTop: position === "top" ? paddingY : 0,
        paddingBottom: position === "bottom" ? paddingY : 0,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: backgroundColor ?? "transparent",
          padding: backgroundColor ? "32px 48px" : 0,
          borderRadius: backgroundColor ? 16 : 0,
          fontFamily,
          fontSize,
          fontWeight,
          color: textColor,
          letterSpacing: -0.5,
          maxWidth: "85%",
          textAlign: "center",
          lineHeight: 1.3,
          whiteSpace: "pre-wrap",
        }}
      >
        {characters.split("").map((c, i) => (
          <React.Fragment key={i}>{c === " " ? "\u00A0" : c}</React.Fragment>
        ))}
        <span
          style={{
            display: "inline-block",
            color: cursorColor,
            marginLeft: 8,
            opacity: showCursor ? 1 : 0,
          }}
        >
          ▌
        </span>
      </div>
    </AbsoluteFill>
  );
};
