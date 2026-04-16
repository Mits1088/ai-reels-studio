import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { Pie } from "@remotion/shapes";

/**
 * ProgressRing — Animated countdown / progress ring for CTA beats.
 *
 * Uses @remotion/shapes Pie with a progress prop to draw a filled arc
 * that sweeps clockwise from 0 → 1 over the beat's duration.
 *
 * Two modes:
 *  - "countdown": ring fills in as time runs (CTA countdown — "follow before it ends")
 *  - "progress":  ring fills in as progress increases (loading, building trust)
 *
 * Frame-driven — no CSS keyframes.
 *
 * Usage:
 *   <ProgressRing durationInFrames={60} radius={80} color="#D97757" />
 *
 * Or in timeline.json overlays lane:
 *   { "type": "ProgressRing", "props": { "radius": 64, "color": "#D97757", "mode": "countdown" } }
 */
export const ProgressRing: React.FC<{
  durationInFrames: number;
  radius?: number;
  color?: string;
  trackColor?: string;
  strokeWidth?: number;
  mode?: "countdown" | "progress";
  /** Position relative to frame center */
  x?: number;
  y?: number;
  /** Pop-in animation on entry */
  withEntryPop?: boolean;
}> = ({
  durationInFrames,
  radius = 72,
  color = "#D97757",
  trackColor = "rgba(255,255,255,0.15)",
  strokeWidth = 10,
  mode = "countdown",
  x = 0,
  y = 0,
  withEntryPop = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Constants ────────────────────────────────────────────────────────────
  // Timing
  const ENTRY_FADE_FRAMES = 3;          // opacity 0→1 on entry
  // Animation
  const ENTRY_SPRING = { damping: 12, stiffness: 280, mass: 0.6 };
  const ENTRY_SCALE_FROM = 0.6;         // scale spring start (pops in from 60%)
  // Layout
  const ARC_STROKE_EXTRA = 2;           // arc is slightly thicker than track so it visually covers it
  // ─────────────────────────────────────────────────────────────────────────

  // Progress: 0 → 1 over duration
  const rawProgress = interpolate(frame, [0, durationInFrames - 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const progress = mode === "countdown" ? rawProgress : rawProgress;

  // Entry pop
  const entryScale = withEntryPop
    ? interpolate(
        spring({ frame, fps, config: ENTRY_SPRING }),
        [0, 1],
        [ENTRY_SCALE_FROM, 1.0]
      )
    : 1;

  const entryOpacity = interpolate(frame, [0, ENTRY_FADE_FRAMES], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const size = (radius + strokeWidth) * 2;
  // Pie uses radius for the full circle; we render two layers:
  // 1. Track ring (full circle at low opacity)
  // 2. Progress arc (Pie with progress prop)

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px)) scale(${entryScale}) rotate(-90deg)`,
        opacity: entryOpacity,
        width: size,
        height: size,
      }}
    >
      {/* Track (background ring) */}
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
      </svg>

      {/* Progress arc — Pie renders a filled sector; we use strokeWidth trick via SVG circle */}
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius - strokeWidth / 2}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth + ARC_STROKE_EXTRA}
          strokeDasharray={`${2 * Math.PI * (radius - strokeWidth / 2)}`}
          strokeDashoffset={`${2 * Math.PI * (radius - strokeWidth / 2) * (1 - progress)}`}
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};
