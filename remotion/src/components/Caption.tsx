import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import type { CaptionToken } from "../types";

interface CaptionProps {
  text: string;
  durationInFrames: number;
  /** Word-level timing tokens from createTikTokStyleCaptions.
   *  When provided, each word highlights at its actual spoken timestamp.
   *  When absent, falls back to equal frame-division per word (legacy). */
  tokens?: CaptionToken[];
}

/**
 * Caption — Mobile-safe subtitle component.
 *
 * Two modes:
 *  1. Token mode (karaoke): each word highlights at its actual spoken timestamp.
 *     Active word scales up + full brightness. Others dimmed. Uses tokens[].
 *  2. Legacy mode: divides durationInFrames equally across words.
 *     Used when tokens are absent (backwards-compatible with existing timelines).
 */
export const Caption: React.FC<CaptionProps> = ({
  text,
  durationInFrames,
  tokens,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Container fade in/out — same for both modes.
  // Short-clip guard: when durationInFrames ≤ 7 the range [0,3,dur-4,dur]
  // is non-monotonic (e.g. [0,3,2,6]), which crashes interpolate().
  // For clips that short, skip the fade and just show at full opacity.
  const containerOpacity =
    durationInFrames > 7
      ? interpolate(
          frame,
          [0, 3, durationInFrames - 4, durationInFrames],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        )
      : 1;

  // ── TOKEN MODE (karaoke) ─────────────────────────────────────────────
  if (tokens && tokens.length > 0) {
    return (
      <TokenCaption
        tokens={tokens}
        durationInFrames={durationInFrames}
        containerOpacity={containerOpacity}
        frame={frame}
        fps={fps}
      />
    );
  }

  // ── LEGACY MODE (frame-division) ─────────────────────────────────────
  const words = text.split(" ").filter(Boolean);
  const framesPerWord = durationInFrames / words.length;
  const currentWordIndex = Math.min(
    Math.floor(frame / framesPerWord),
    words.length - 1
  );
  const word = words[currentWordIndex];
  const wordStart = currentWordIndex * framesPerWord;
  const localFrame = frame - wordStart;
  const isEmphasis =
    word === word.toUpperCase() && word.length > 1 && /[A-Z]/.test(word);

  const s = spring({
    frame: localFrame,
    fps,
    config: { damping: 18, stiffness: 280, mass: 0.6 },
  });

  return (
    <div style={containerStyle(containerOpacity)}>
      <div
        key={currentWordIndex}
        style={pillStyle(isEmphasis, s)}
      >
        <span style={wordStyle(isEmphasis, s)}>{word}</span>
      </div>
    </div>
  );
};

// ── Token (karaoke) sub-component ──────────────────────────────────────

const TokenCaption: React.FC<{
  tokens: CaptionToken[];
  durationInFrames: number;
  containerOpacity: number;
  frame: number;
  fps: number;
}> = ({ tokens, durationInFrames, containerOpacity, frame, fps }) => {
  // Convert frame → ms relative to the start of this Sequence (frame 0 = start of caption)
  // The Sequence wraps us so frame 0 is the caption's start time.
  // tokens[].fromMs / toMs are absolute transcript ms — we need to know
  // the caption page's startMs to make them relative. We compute it from
  // the first token's fromMs.
  const pageStartMs = tokens[0].fromMs;
  const currentMs = (frame / 30) * 1000 + pageStartMs;

  // Find which token is currently active
  const activeIdx = tokens.findIndex(
    (t) => currentMs >= t.fromMs && currentMs < t.toMs
  );
  // If we're past all tokens (slight overhang), keep last word active
  const resolvedIdx =
    activeIdx === -1 && currentMs >= tokens[tokens.length - 1].fromMs
      ? tokens.length - 1
      : activeIdx;

  return (
    <div style={containerStyle(containerOpacity)}>
      <div style={karaokePageStyle}>
        {tokens.map((token, i) => {
          const isActive = i === resolvedIdx;
          const isPast = i < resolvedIdx;
          // Spring for active word pop-in: only runs when this token becomes active
          const tokenFrame = isActive
            ? Math.max(0, Math.round(((currentMs - token.fromMs) / 1000) * fps))
            : 0;
          const s = isActive
            ? spring({ frame: tokenFrame, fps, config: { damping: 18, stiffness: 320, mass: 0.5 } })
            : 1;

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                marginRight: 6,
                fontSize: isActive ? interpolate(s, [0, 1], [52, 58]) : 52,
                fontWeight: isActive ? 900 : isPast ? 700 : 600,
                fontFamily: "'Inter', 'Segoe UI', sans-serif",
                letterSpacing: "-0.02em",
                color: isActive ? "#FFFFFF" : isPast ? "rgba(255,255,255,0.55)" : "rgba(255,255,255,0.4)",
                textShadow: isActive
                  ? "0 2px 12px rgba(0,0,0,0.7)"
                  : "0 1px 4px rgba(0,0,0,0.4)",
                transform: isActive ? `scale(${interpolate(s, [0, 1], [0.88, 1.0])})` : "scale(1)",
                transformOrigin: "center bottom",
                transition: "color 0.08s ease",
              }}
            >
              {token.text.trim()}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// ── Shared styles ─────────────────────────────────────────────────────

const containerStyle = (opacity: number): React.CSSProperties => ({
  position: "absolute",
  bottom: 320,
  left: 48,
  right: 48,
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 60,
  opacity,
});

const karaokePageStyle: React.CSSProperties = {
  background: "rgba(0, 0, 0, 0.72)",
  borderRadius: 20,
  padding: "14px 32px",
  border: "1px solid rgba(255, 255, 255, 0.06)",
  boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
  display: "flex",
  flexWrap: "wrap",
  justifyContent: "center",
  alignItems: "baseline",
  maxWidth: "90%",
  lineHeight: 1.3,
};

const pillStyle = (isEmphasis: boolean, s: number): React.CSSProperties => ({
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
});

const wordStyle = (isEmphasis: boolean, s: number): React.CSSProperties => ({
  fontSize: isEmphasis ? 62 : 54,
  fontWeight: isEmphasis ? 900 : 700,
  fontFamily: "'Inter', 'Segoe UI', sans-serif",
  letterSpacing: isEmphasis ? "0.02em" : "-0.02em",
  color: isEmphasis ? "#00E5FF" : "#FFFFFF",
  textShadow: isEmphasis
    ? "0 0 20px rgba(0, 229, 255, 0.5)"
    : "0 2px 8px rgba(0,0,0,0.6)",
  whiteSpace: "nowrap",
});
