/**
 * ToastCard — vendored from clippkit (MIT)
 * Source: https://github.com/reactvideoeditor/clippkit
 *         apps/docs/registry/default/components/toast-card.tsx
 *
 * Adapted for the AI Reels Studio pipeline:
 *  - Named export instead of default
 *  - Replaced CSS variable defaults with explicit theme colors
 *  - Wraps in AbsoluteFill for OVERLAY_REGISTRY use
 *
 * Use it for trust beat sub-cards (alternative to CardStack), brief
 * notification-style proof moments, or "this just happened" callouts.
 * Spring entry from one of 5 corner positions, spring exit in the same
 * direction. Self-contained — no parent positioning needed.
 */
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type ToastPosition =
  | "bottom-left"
  | "bottom-right"
  | "top-left"
  | "top-right"
  | "center";

interface ToastCardProps {
  title?: string;
  message?: string;
  titleColor?: string;
  messageColor?: string;
  backgroundColor?: string;
  titleFontSize?: string;
  messageFontSize?: string;
  width?: string;
  padding?: string;
  borderRadius?: string;
  borderColor?: string;
  borderWidth?: string;
  boxShadow?: string;
  positionPreset?: ToastPosition;
  margin?: string;
  entryDurationInFrames?: number;
  visibleDurationInFrames?: number;
  exitDurationInFrames?: number;
  damping?: number;
  mass?: number;
  stiffness?: number;
  fontFamily?: string;
  slideOffset?: number;
  durationInFrames?: number;
}

export const ToastCard: React.FC<ToastCardProps> = ({
  title = "Success",
  message = "Your action was completed.",
  titleColor = "#1A1A1A",
  messageColor = "#1A1A1A",
  backgroundColor = "#FFFFFF",
  titleFontSize = "1.6rem",
  messageFontSize = "1.1rem",
  width = "440px",
  padding = "26px 32px",
  borderRadius = "20px",
  borderColor = "rgba(0,0,0,0.08)",
  borderWidth = "1px",
  boxShadow = "0 16px 48px rgba(0,0,0,0.18), 0 4px 12px rgba(0,0,0,0.08)",
  positionPreset = "bottom-left",
  margin = "60px",
  entryDurationInFrames = 12,
  visibleDurationInFrames = 60,
  exitDurationInFrames = 10,
  damping = 18,
  mass = 0.7,
  stiffness = 200,
  fontFamily = "'Inter', system-ui, -apple-system, sans-serif",
  slideOffset = 60,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // If durationInFrames is passed by the OVERLAY_REGISTRY, derive
  // entry / visible / exit from it. Otherwise use explicit props.
  let entryDur = entryDurationInFrames;
  let visibleDur = visibleDurationInFrames;
  let exitDur = exitDurationInFrames;
  if (durationInFrames !== undefined) {
    entryDur = Math.min(12, Math.floor(durationInFrames * 0.2));
    exitDur = Math.min(10, Math.floor(durationInFrames * 0.15));
    visibleDur = Math.max(0, durationInFrames - entryDur - exitDur);
  }

  const exitStart = entryDur + visibleDur;

  const entryProgress = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    durationInFrames: entryDur,
    config: { damping, mass, stiffness },
  });

  const exitProgress = spring({
    frame: frame - exitStart,
    fps,
    from: 0,
    to: 1,
    durationInFrames: exitDur,
    config: { damping, mass, stiffness: stiffness / 1.5 },
  });

  const opacity =
    interpolate(entryProgress, [0, 1], [0, 1]) *
    interpolate(exitProgress, [0, 1], [1, 0]);

  let yTranslateStart = 0;
  if (positionPreset === "bottom-left" || positionPreset === "bottom-right") {
    yTranslateStart = slideOffset;
  } else if (positionPreset === "top-left" || positionPreset === "top-right") {
    yTranslateStart = -slideOffset;
  } else if (positionPreset === "center") {
    yTranslateStart = slideOffset;
  }

  const yPos =
    interpolate(entryProgress, [0, 1], [yTranslateStart, 0]) +
    interpolate(exitProgress, [0, 1], [0, yTranslateStart]);

  const scaleStart = 0.95;
  const scaleEnd = 1;
  const scale =
    positionPreset === "center"
      ? interpolate(entryProgress, [0, 1], [scaleStart, scaleEnd]) *
        interpolate(exitProgress, [0, 1], [scaleEnd, scaleStart])
      : 1;

  const transformProperties: string[] = [];
  if (positionPreset === "center") {
    transformProperties.push("translate(-50%, -50%)");
  }
  transformProperties.push(`translateY(${yPos}px)`);
  if (scale !== 1) {
    transformProperties.push(`scale(${scale})`);
  }

  const cardStyle: React.CSSProperties = {
    position: "absolute",
    width,
    padding,
    background: backgroundColor,
    borderRadius,
    borderColor,
    borderWidth,
    borderStyle: "solid",
    boxShadow,
    fontFamily,
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    boxSizing: "border-box",
    opacity,
    transform: transformProperties.join(" "),
  };

  if (positionPreset === "center") {
    cardStyle.top = "50%";
    cardStyle.left = "50%";
  } else {
    if (positionPreset.includes("bottom")) cardStyle.bottom = margin;
    if (positionPreset.includes("top")) cardStyle.top = margin;
    if (positionPreset.includes("left")) {
      cardStyle.left = margin;
      cardStyle.right = "auto";
    }
    if (positionPreset.includes("right")) {
      cardStyle.right = margin;
      cardStyle.left = "auto";
    }
  }

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={cardStyle}>
        {title && (
          <div
            style={{
              margin: 0,
              fontSize: titleFontSize,
              fontWeight: 800,
              color: titleColor,
              letterSpacing: -0.3,
            }}
          >
            {title}
          </div>
        )}
        {message && (
          <div
            style={{
              margin: 0,
              fontSize: messageFontSize,
              color: messageColor,
              opacity: 0.78,
              fontWeight: 500,
            }}
          >
            {message}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
