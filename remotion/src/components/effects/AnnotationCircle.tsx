import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";
import { evolvePath } from "@remotion/paths";

/**
 * AnnotationCircle — Hand-drawn-style annotation drawn on screen.
 *
 * Powered by @remotion/paths evolvePath() for frame-accurate path drawing.
 * Supports two shapes:
 *   - "ellipse" (default) — wobbly circle drawn around a UI element
 *   - "underline" — horizontal underline drawn left-to-right under text
 *
 * Used in editorial-authority style to call attention to buttons, fields,
 * or UI elements in proof screenshots.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const AnnotationCircle: React.FC<{
  /** Center X as percentage (0-100) of the 1080px frame width */
  x: number;
  /** Center Y as percentage (0-100) of the 1920px frame height */
  y: number;
  /** Shape variant. Default: "ellipse" */
  shape?: "ellipse" | "underline";
  /** Horizontal radius in pixels (ellipse only) */
  radiusX?: number;
  /** Vertical radius in pixels (ellipse only) */
  radiusY?: number;
  /** Width of the underline in pixels (underline only) */
  underlineWidth?: number;
  /** Y offset below the baseline in pixels (underline only). Default 8. */
  underlineOffsetY?: number;
  color?: string;
  strokeWidth?: number;
  /** Frames to draw the annotation. Default 10. */
  drawDuration?: number;
  durationInFrames: number;
  /** Unique seed for wobble randomization (ellipse only). Default "annot-0". */
  seed?: string;
}> = ({
  x,
  y,
  shape = "ellipse",
  radiusX = 60,
  radiusY = 40,
  underlineWidth = 200,
  underlineOffsetY = 8,
  color = "#22C55E",
  strokeWidth = 3,
  drawDuration = 10,
  durationInFrames,
  seed = "annot-0",
}) => {
  const frame = useCurrentFrame();

  // ── Draw progress (0 → 1) ──
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

  // ── Build the SVG path string based on shape ──
  const pathData = React.useMemo(() => {
    if (shape === "underline") {
      // Horizontal line in 1080×1920 coordinate space
      const cx = (x / 100) * 1080;
      const cy = (y / 100) * 1920 + underlineOffsetY;
      const half = underlineWidth / 2;
      return `M ${cx - half} ${cy} L ${cx + half} ${cy}`;
    }

    // Ellipse with hand-drawn wobble
    const points = 36;
    const cx = (x / 100) * 1080;
    const cy = (y / 100) * 1920;
    const pts: string[] = [];
    for (let i = 0; i <= points; i++) {
      const angle = (i / points) * Math.PI * 2;
      const wobbleR = 1 + (random(`${seed}-r-${i}`) - 0.5) * 0.15;
      const px = cx + Math.cos(angle) * radiusX * wobbleR;
      const py = cy + Math.sin(angle) * radiusY * wobbleR;
      pts.push(`${i === 0 ? "M" : "L"} ${px.toFixed(1)} ${py.toFixed(1)}`);
    }
    pts.push("Z");
    return pts.join(" ");
  }, [shape, x, y, radiusX, radiusY, underlineWidth, underlineOffsetY, seed]);

  // ── evolvePath: accurate strokeDasharray + strokeDashoffset for any path ──
  const { strokeDasharray, strokeDashoffset } = evolvePath(drawProgress, pathData);

  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 55, opacity: exitOpacity }}>
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 1080 1920"
        style={{ position: "absolute", inset: 0 }}
      >
        <path
          d={pathData}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
    </AbsoluteFill>
  );
};
