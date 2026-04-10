import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

/**
 * CursorClick — Cursor icon with click ripple animation at a specified coordinate.
 *
 * Used in editorial-authority style to simulate clicking a button or UI element
 * on a proof screenshot. The cursor appears, clicks, and a ripple expands.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const CursorClick: React.FC<{
  /** Horizontal position as percentage (0-100) */
  x: number;
  /** Vertical position as percentage (0-100) */
  y: number;
  durationInFrames: number;
  /** Frames before cursor appears */
  cursorDelay?: number;
  /** Frame when click ripple fires (relative to cursor appearance) */
  clickFrame?: number;
  cursorColor?: string;
  rippleColor?: string;
  cursorSize?: number;
}> = ({
  x,
  y,
  durationInFrames,
  cursorDelay = 0,
  clickFrame = 8,
  cursorColor = "#1A1A1A",
  rippleColor = "rgba(0,0,0,0.15)",
  cursorSize = 24,
}) => {
  const frame = useCurrentFrame();

  const localFrame = frame - cursorDelay;
  if (localFrame < 0) return null;

  // ── Cursor fade in ──
  const cursorOpacity = interpolate(localFrame, [0, 3], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Cursor exit ──
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 4, durationInFrames - 1],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── Click ripple ──
  const rippleFrame = localFrame - clickFrame;
  const rippleDuration = 10;
  const showRipple = rippleFrame >= 0 && rippleFrame <= rippleDuration;

  const rippleRadius = showRipple
    ? interpolate(rippleFrame, [0, rippleDuration], [0, 50], {
        extrapolateRight: "clamp",
      })
    : 0;

  const rippleOpacity = showRipple
    ? interpolate(rippleFrame, [0, rippleDuration * 0.3, rippleDuration], [0.5, 0.35, 0], {
        extrapolateRight: "clamp",
      })
    : 0;

  // ── Cursor press (slight scale down on click) ──
  const pressScale =
    rippleFrame >= 0 && rippleFrame < 4
      ? interpolate(rippleFrame, [0, 2, 4], [1.0, 0.85, 1.0], {
          extrapolateRight: "clamp",
        })
      : 1;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 60,
        opacity: cursorOpacity * exitOpacity,
      }}
    >
      {/* Ripple */}
      {showRipple && (
        <div
          style={{
            position: "absolute",
            left: `${x}%`,
            top: `${y}%`,
            width: rippleRadius * 2,
            height: rippleRadius * 2,
            borderRadius: "50%",
            backgroundColor: rippleColor,
            opacity: rippleOpacity,
            transform: "translate(-50%, -50%)",
          }}
        />
      )}

      {/* Cursor arrow (SVG) */}
      <div
        style={{
          position: "absolute",
          left: `${x}%`,
          top: `${y}%`,
          transform: `scale(${pressScale})`,
          transformOrigin: "top left",
        }}
      >
        <svg
          width={cursorSize}
          height={cursorSize * 1.3}
          viewBox="0 0 24 32"
          fill="none"
        >
          {/* Cursor arrow shape */}
          <path
            d="M2 2L2 26L8.5 19.5L14 29L18 27L12.5 17.5L21 17.5L2 2Z"
            fill={cursorColor}
            stroke="#FFFFFF"
            strokeWidth={2}
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </AbsoluteFill>
  );
};
