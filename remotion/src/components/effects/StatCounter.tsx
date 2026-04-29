import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

/**
 * StatCounter — animated number count-up from startValue to value.
 *
 * Renders as a centered overlay (AbsoluteFill, transparent background).
 * Use over a dark avatar beat or GradientMesh background.
 *
 * Example timeline.json:
 * {
 *   "type": "StatCounter",
 *   "start": 4.2,
 *   "end": 7.8,
 *   "props": {
 *     "value": 6,
 *     "suffix": "x",
 *     "label": "faster than GPT-4",
 *     "color": "#D97757"
 *   }
 * }
 */
export const StatCounter: React.FC<{
  /** Target number to count up to */
  value: number;
  /** Starting value (default 0) */
  startValue?: number;
  /** Text below the number (e.g. "faster than GPT-4") */
  label?: string;
  /** Prepended to the number (e.g. "$", "+") */
  prefix?: string;
  /** Appended to the number (e.g. "x", "%", "ms") */
  suffix?: string;
  /** Accent color for the number (default: brand orange) */
  color?: string;
  fontSize?: number;
  labelFontSize?: number;
  durationInFrames: number;
}> = ({
  value,
  startValue = 0,
  label,
  prefix = "",
  suffix = "",
  color = "#D97757",
  fontSize = 160,
  labelFontSize = 52,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entry: spring scale-pop ──────────────────────────────────────────────
  const entrySpring = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 300, mass: 0.6 },
  });
  const entryScale = interpolate(entrySpring, [0, 1], [0.78, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const entryOpacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit ─────────────────────────────────────────────────────────────────
  const safeExit = Math.max(0, durationInFrames - 4);
  const exitOpacity = interpolate(
    frame,
    [safeExit, Math.max(safeExit + 1, durationInFrames)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Count animation: starts at frame 5, finishes ~15 frames before end ──
  const countEnd = Math.max(10, durationInFrames - 15);
  const raw = interpolate(frame, [5, countEnd], [startValue, value], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Integer vs decimal display
  const isInteger = Number.isInteger(value) && Number.isInteger(startValue);
  const displayValue = isInteger
    ? Math.round(raw).toLocaleString()
    : raw.toFixed(1);

  // ── Label opacity (staggered slightly after number) ─────────────────────
  const labelOpacity = interpolate(frame, [8, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: entryOpacity * exitOpacity,
      }}
    >
      <div
        style={{
          transform: `scale(${entryScale})`,
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {/* ── Number row ───────────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "center",
            gap: 4,
            fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
            fontWeight: 900,
            letterSpacing: -4,
            lineHeight: 1,
          }}
        >
          {prefix && (
            <span style={{ fontSize: fontSize * 0.52, color, opacity: 0.8 }}>
              {prefix}
            </span>
          )}
          <span style={{ fontSize, color }}>{displayValue}</span>
          {suffix && (
            <span style={{ fontSize: fontSize * 0.52, color, opacity: 0.8 }}>
              {suffix}
            </span>
          )}
        </div>

        {/* ── Label ────────────────────────────────────────────────── */}
        {label && (
          <div
            style={{
              marginTop: 18,
              fontSize: labelFontSize,
              fontWeight: 500,
              color: "rgba(255,255,255,0.68)",
              fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
              letterSpacing: -0.5,
              opacity: labelOpacity,
              maxWidth: 840,
              textAlign: "center",
              lineHeight: 1.3,
            }}
          >
            {label}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
