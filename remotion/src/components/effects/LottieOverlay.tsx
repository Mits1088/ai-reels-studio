import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Lottie, type LottieAnimationData } from "@remotion/lottie";

/**
 * LottieOverlay — Animated brand logo using a Lottie JSON file.
 *
 * Drop-in replacement for LogoOverlay when an animated Lottie version of
 * the brand asset is available. Uses the same positioning API as LogoOverlay
 * so they can be swapped without changing other props.
 *
 * How to source Lottie brand animations:
 *   - LottieFiles.com → search brand name → download as JSON
 *   - Brand's own design resources page (Anthropic, Google, etc.)
 *   - Official product launch pages often include Lottie hero animations
 *
 * Place the JSON file in remotion/public/brands/<Brand>.json
 * Reference it as: src="brands/Anthropic.json"
 *
 * Frame-driven animation — delayRender pauses Remotion until JSON loads.
 */
export const LottieOverlay: React.FC<{
  /** Path relative to remotion/public/. E.g. "brands/Anthropic.json" */
  src: string;
  durationInFrames: number;
  /** Whether the Lottie animation loops. Default false (plays once). */
  loop?: boolean;
  /** Animation speed multiplier. Default 1.0. */
  playbackRate?: number;
  /** Rendered size in pixels (square). Default 280. */
  size?: number;
  /** Vertical position. Default "center-top". */
  position?: "center-top" | "center" | "center-bottom";
  /** Padding from the top/bottom edge (px). Default 200. */
  paddingY?: number;
  /** Horizontal position. Default "center". */
  horizontal?: "left" | "center" | "right";
  /** Padding from the left/right edge (px). Default 0. */
  paddingX?: number;
  /** Optional white card behind the animation. Default true. */
  withBackground?: boolean;
  backgroundColor?: string;
  borderRadius?: number;
}> = ({
  src,
  durationInFrames,
  loop = false,
  playbackRate = 1,
  size = 280,
  position = "center-top",
  paddingY = 200,
  horizontal = "center",
  paddingX = 0,
  withBackground = true,
  backgroundColor = "#FAF9F5",
  borderRadius = 28,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Async Lottie JSON load ──
  const [handle] = useState(() => delayRender(`Loading Lottie: ${src}`));
  const [animationData, setAnimationData] = useState<LottieAnimationData | null>(null);

  useEffect(() => {
    fetch(staticFile(src))
      .then((res) => res.json())
      .then((json) => {
        setAnimationData(json);
        continueRender(handle);
      })
      .catch((err) => {
        cancelRender(err);
      });
  }, [handle, src]);

  // ── Spring scale-pop entry (matches LogoOverlay) ──
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

  // ── Positioning (same system as LogoOverlay) ──
  const justifyContent =
    position === "center-top"
      ? "flex-start"
      : position === "center-bottom"
        ? "flex-end"
        : "center";

  const paddingTop = position === "center-top" ? paddingY : 0;
  const paddingBottom = position === "center-bottom" ? paddingY : 0;

  const alignItems =
    horizontal === "left"
      ? "flex-start"
      : horizontal === "right"
        ? "flex-end"
        : "center";

  const paddingLeft = horizontal === "left" ? paddingX : 0;
  const paddingRight = horizontal === "right" ? paddingX : 0;

  if (!animationData) return null;

  return (
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
          transform: `scale(${entryScale})`,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Lottie
          animationData={animationData}
          loop={loop}
          playbackRate={playbackRate}
          style={{ width: size, height: size }}
        />
      </div>
    </AbsoluteFill>
  );
};
