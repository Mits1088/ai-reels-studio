import React from "react";
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { Trail } from "@remotion/motion-blur";

/**
 * LogoOverlay — Small brand logo overlay with optional background card.
 *
 * Renders an SVG/PNG image (typically a brand logo from `public/brands/`)
 * at a specific position with a spring scale-pop entry, optional rounded
 * background card for contrast against busy backgrounds, and a clean exit.
 *
 * Used for hook brand walls and small customer-wall accents where a text
 * BadgePopup would be too generic. Pairs well with:
 *   - LobeHub Mono SVGs (use `color` to set the fill via currentColor)
 *   - Simple Icons SVGs (already colored, leave color undefined)
 *   - PNG product marks
 *
 * trail={true} — adds a motion blur trail effect to the bounce animation.
 * Use on hook bouncing logos for energy (3-5 layers, lagInFrames 0.2-0.4).
 * Do not use trail on static (non-bouncing) logos — no benefit.
 *
 * For Lottie-animated brand logos, use LottieOverlay instead.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const LogoOverlay: React.FC<{
  src: string;
  durationInFrames: number;
  /** Pixel width of the logo (height auto-derived from aspect ratio). */
  size?: number;
  /** Vertical position. */
  position?: "center-top" | "center" | "center-bottom";
  /** When position is center-top/bottom, the padding from the edge. */
  paddingY?: number;
  /** Horizontal position. Default "center". */
  horizontal?: "left" | "center" | "right";
  /** When horizontal is left/right, the inset from that edge. */
  paddingX?: number;
  /** Optional background card behind the logo for contrast. */
  withBackground?: boolean;
  backgroundColor?: string;
  /** CSS color applied to the SVG via currentColor (LobeHub Mono variant). */
  color?: string;
  /** Border radius of the optional background card. */
  borderRadius?: number;
  /** Continuous bounce animation (jumping up and down). Default false. */
  bounce?: boolean;
  /** Bounce amplitude in pixels. Default 30. */
  bounceAmplitude?: number;
  /** Bounce frequency in Hz (bounces per second). Default 2.5. */
  bounceFrequency?: number;
  /**
   * Enable motion trail on the bounce animation (@remotion/motion-blur Trail).
   * Only has visual effect when bounce={true}. Default false.
   * Adds trailing ghost copies behind the logo as it moves, amplifying hook energy.
   */
  trail?: boolean;
  /**
   * Number of trail ghost layers. Lower = subtle, higher = dramatic.
   * Default 4. Max recommended: 8.
   */
  trailLayers?: number;
  /**
   * Frames each trail layer lags behind the previous.
   * Default 0.3. Higher = longer, more visible trail.
   */
  trailLagInFrames?: number;
}> = ({
  src,
  durationInFrames,
  size = 320,
  position = "center-top",
  paddingY = 200,
  horizontal = "center",
  paddingX = 0,
  withBackground = true,
  backgroundColor = "#FAF9F5",
  color,
  borderRadius = 28,
  bounce = false,
  bounceAmplitude = 30,
  bounceFrequency = 2.5,
  trail = false,
  trailLayers = 4,
  trailLagInFrames = 0.3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Spring scale-pop entry ──
  const s = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 200, mass: 0.7 },
  });
  const entryScale = interpolate(s, [0, 1], [0.6, 1.0]);

  const entryOpacity = interpolate(frame, [0, 3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit fade ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 3, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Bounce animation (continuous sine wave) ──
  // Uses abs(sin) for a "ball bouncing" pattern: 0 at rest, -amplitude at peak.
  const bounceY = bounce
    ? -Math.abs(
        Math.sin((frame / fps) * 2 * Math.PI * bounceFrequency)
      ) * bounceAmplitude
    : 0;

  // ── Vertical position mapping ──
  const justifyContent =
    position === "center-top"
      ? "flex-start"
      : position === "center-bottom"
        ? "flex-end"
        : "center";

  const paddingTop = position === "center-top" ? paddingY : 0;
  const paddingBottom = position === "center-bottom" ? paddingY : 0;

  // ── Horizontal position mapping ──
  const alignItems =
    horizontal === "left"
      ? "flex-start"
      : horizontal === "right"
        ? "flex-end"
        : "center";

  const paddingLeft = horizontal === "left" ? paddingX : 0;
  const paddingRight = horizontal === "right" ? paddingX : 0;

  const content = (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems,
        justifyContent,
        paddingTop,
        paddingBottom,
        paddingLeft,
        paddingRight,
        zIndex: 30,
        opacity: entryOpacity * exitOpacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: withBackground ? backgroundColor : "transparent",
          padding: withBackground ? "36px 56px" : 0,
          borderRadius: withBackground ? borderRadius : 0,
          boxShadow: withBackground
            ? "0 12px 40px rgba(0, 0, 0, 0.18), 0 2px 8px rgba(0, 0, 0, 0.06)"
            : "none",
          transform: `translateY(${bounceY}px) scale(${entryScale})`,
          // currentColor for LobeHub Mono SVGs (fill="currentColor")
          color: color ?? "#1A1A1A",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{
            width: size,
            height: "auto",
            display: "block",
          }}
        />
      </div>
    </AbsoluteFill>
  );

  // Trail wraps the entire AbsoluteFill — AbsoluteFill is position:absolute
  // so it satisfies Trail's requirement for absolutely-positioned children.
  // Only apply when bounce is active — trail on a static logo has no effect.
  if (trail && bounce) {
    return (
      <Trail
        layers={trailLayers}
        lagInFrames={trailLagInFrames}
        trailOpacity={0.5}
      >
        {content}
      </Trail>
    );
  }

  return content;
};
