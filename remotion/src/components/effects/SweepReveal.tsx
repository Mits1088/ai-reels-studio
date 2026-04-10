import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from "remotion";

/**
 * SweepReveal — A light sweep that wipes across the screen to reveal content.
 * Wraps children — content is hidden until the sweep passes.
 * Used for dramatic reveals of new scenes or important content.
 *
 * Props:
 * - direction: sweep direction
 * - sweepColor: the color of the light band
 * - revealFrames: how many frames the reveal takes
 */
export const SweepReveal: React.FC<{
  children: React.ReactNode;
  direction?: "left-to-right" | "right-to-left" | "top-to-bottom";
  sweepColor?: string;
  revealFrames?: number;
  durationInFrames: number;
}> = ({
  children,
  direction = "left-to-right",
  sweepColor = "rgba(0, 229, 255, 0.5)",
  revealFrames = 6,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(frame, [0, revealFrames], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  // Exit
  const exitOpacity = interpolate(frame, [durationInFrames - 3, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  let clipPath = "";
  let sweepPos = 0;
  let sweepStyle: React.CSSProperties = {};

  switch (direction) {
    case "left-to-right":
      clipPath = `inset(0 ${100 - progress * 100}% 0 0)`;
      sweepPos = progress * 100;
      sweepStyle = {
        position: "absolute",
        top: 0, bottom: 0,
        left: `${sweepPos - 3}%`,
        width: "6%",
        background: `linear-gradient(90deg, transparent, ${sweepColor}, transparent)`,
        zIndex: 1,
        opacity: progress < 0.95 ? 0.8 : 0,
      };
      break;
    case "right-to-left":
      clipPath = `inset(0 0 0 ${100 - progress * 100}%)`;
      sweepPos = 100 - progress * 100;
      sweepStyle = {
        position: "absolute",
        top: 0, bottom: 0,
        left: `${sweepPos - 3}%`,
        width: "6%",
        background: `linear-gradient(90deg, transparent, ${sweepColor}, transparent)`,
        zIndex: 1,
        opacity: progress < 0.95 ? 0.8 : 0,
      };
      break;
    case "top-to-bottom":
      clipPath = `inset(0 0 ${100 - progress * 100}% 0)`;
      sweepPos = progress * 100;
      sweepStyle = {
        position: "absolute",
        left: 0, right: 0,
        top: `${sweepPos - 2}%`,
        height: "4%",
        background: `linear-gradient(180deg, transparent, ${sweepColor}, transparent)`,
        zIndex: 1,
        opacity: progress < 0.95 ? 0.8 : 0,
      };
      break;
  }

  return (
    <div style={{ position: "relative", width: "100%", height: "100%", opacity: exitOpacity }}>
      <div style={{ width: "100%", height: "100%", clipPath }}>
        {children}
      </div>
      <div style={sweepStyle} />
    </div>
  );
};
