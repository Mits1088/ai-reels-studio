import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

/**
 * PunchText — Slam-in with echo ripple.
 *
 * Main text scales down fast from 2.5x → 1.0x (the slam).
 * On impact, 3 echo copies ripple outward — each scales up
 * from 1.0x and fades to 0, staggered by a few frames.
 * Creates a shockwave / echo pulse effect.
 *
 * All animation driven by useCurrentFrame() + spring() + interpolate().
 */

const ECHO_COUNT = 3;
const ECHO_STAGGER = 4;       // frames between each echo start
const ECHO_DURATION = 16;     // frames each echo lives
const ECHO_MAX_SCALE = 1.35;  // how far each echo expands
const IMPACT_FRAME = 6;       // frame when slam lands (echoes start)

export const PunchText: React.FC<{
  text: string;
  durationInFrames: number;
  color?: string;
  fontSize?: number;
  flashColor?: string;
}> = ({
  text,
  durationInFrames,
  color = "#34A853",
  fontSize = 130,
  flashColor = "#FFFFFF",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Main text slam ──
  const slamProgress = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 350, mass: 0.5 },
  });

  const mainScale = interpolate(slamProgress, [0, 1], [2.5, 1.0]);
  const mainOpacity = interpolate(frame, [0, 2], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Letter spacing tightens on slam
  const letterSpacing = interpolate(slamProgress, [0, 1], [40, 2]);

  // White flash on impact
  const flashOpacity = interpolate(frame, [4, 6, 9, 14], [0, 0.5, 0.2, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Subtle breathe while holding
  const breathe =
    frame > 15 ? 1 + Math.sin((frame - 15) * 0.1) * 0.012 : 1;

  // Fade out at end
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 8, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Echo ripples ──
  const echoes = Array.from({ length: ECHO_COUNT }, (_, i) => {
    const echoStart = IMPACT_FRAME + i * ECHO_STAGGER;
    const echoFrame = frame - echoStart;

    if (echoFrame < 0 || echoFrame > ECHO_DURATION) return null;

    const echoProgress = interpolate(
      echoFrame,
      [0, ECHO_DURATION],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );

    const echoScale = interpolate(echoProgress, [0, 1], [1.0, ECHO_MAX_SCALE + i * 0.08]);
    const echoOpacity = interpolate(echoProgress, [0, 0.15, 1], [0, 0.35 - i * 0.08, 0]);

    return (
      <span
        key={`echo-${i}`}
        style={{
          position: "absolute",
          fontSize,
          fontWeight: 900,
          color: "transparent",
          fontFamily: "system-ui, -apple-system, sans-serif",
          WebkitTextStroke: `2px ${color}`,
          transform: `scale(${echoScale})`,
          opacity: echoOpacity,
          letterSpacing: 2,
          pointerEvents: "none",
        }}
      >
        {text}
      </span>
    );
  });

  const textStyle: React.CSSProperties = {
    fontSize,
    fontWeight: 900,
    color,
    fontFamily: "system-ui, -apple-system, sans-serif",
    transform: `scale(${mainScale * breathe})`,
    letterSpacing,
    textShadow: `0 0 50px ${color}77, 0 0 100px ${color}44, 0 6px 24px rgba(0,0,0,0.6)`,
  };

  return (
    <>
      {/* White flash */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: flashColor,
          opacity: flashOpacity,
          zIndex: 55,
          pointerEvents: "none",
        }}
      />

      {/* Text + echoes container */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 56,
          opacity: mainOpacity * fadeOut,
        }}
      >
        {/* Echo layers (behind main text) */}
        {echoes}

        {/* Main text */}
        <span style={textStyle}>{text}</span>
      </div>
    </>
  );
};
