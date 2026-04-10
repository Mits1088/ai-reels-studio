import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

/**
 * AnnotationCircle — Hand-drawn-style circle drawn around a UI element.
 *
 * Draws an ellipse via SVG stroke-dashoffset, with slight wobble in the
 * path for a hand-drawn feel. Used in editorial-authority style to
 * call attention to buttons, fields, or UI elements in proof screenshots.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const AnnotationCircle: React.FC<{
  /** Center X as percentage (0-100) */
  x: number;
  /** Center Y as percentage (0-100) */
  y: number;
  /** Horizontal radius in pixels */
  radiusX?: number;
  /** Vertical radius in pixels */
  radiusY?: number;
  color?: string;
  strokeWidth?: number;
  /** Frames to draw the circle */
  drawDuration?: number;
  durationInFrames: number;
  /** Unique seed for wobble randomization */
  seed?: string;
}> = ({
  x,
  y,
  radiusX = 60,
  radiusY = 40,
  color = "#22C55E",
  strokeWidth = 3,
  drawDuration = 10,
  durationInFrames,
  seed = "annot-0",
}) => {
  const frame = useCurrentFrame();

  // ── Draw progress ──
  const drawProgress = interpolate(frame, [0, drawDuration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit fade ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 4, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Generate a hand-drawn ellipse path with wobble ──
  const points = 36;
  const pathData = React.useMemo(() => {
    const pts: string[] = [];
    for (let i = 0; i <= points; i++) {
      const angle = (i / points) * Math.PI * 2;
      const wobbleR = 1 + (random(`${seed}-r-${i}`) - 0.5) * 0.15;
      const px = Math.cos(angle) * radiusX * wobbleR;
      const py = Math.sin(angle) * radiusY * wobbleR;
      pts.push(`${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`);
    }
    pts.push("Z");
    return pts.join(" ");
  }, [radiusX, radiusY, seed]);

  // Approximate circumference for stroke-dasharray
  const circumference = Math.PI * 2 * Math.max(radiusX, radiusY) * 1.1;
  const dashOffset = circumference * (1 - drawProgress);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 55, opacity: exitOpacity }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1080 1920"
        style={{ position: "absolute", inset: 0 }}
      >
        <g
          transform={`translate(${(x / 100) * 1080}, ${(y / 100) * 1920})`}
        >
          <path
            d={pathData}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
          />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
