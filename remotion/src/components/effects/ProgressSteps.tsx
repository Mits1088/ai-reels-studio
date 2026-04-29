import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface ProgressStep {
  label: string;
  sublabel?: string;
  color?: string;
}

/**
 * ProgressSteps — Animated numbered step list with connecting line.
 *
 * Steps appear sequentially with a spring entry, connected by a vertical
 * line that draws down as each step reveals.
 *
 * Example timeline.json overlay:
 * {
 *   "type": "ProgressSteps",
 *   "start": 3.0,
 *   "end": 9.0,
 *   "props": {
 *     "accentColor": "#D97757",
 *     "steps": [
 *       { "label": "Upload your resume" },
 *       { "label": "Claude reads every line", "sublabel": "in seconds" },
 *       { "label": "Get your personalised plan" }
 *     ]
 *   }
 * }
 */
export const ProgressSteps: React.FC<{
  steps: ProgressStep[];
  /** Accent/primary color for circles and active state (default: brand orange) */
  accentColor?: string;
  /** Frames between each step's spring start (default 10) */
  staggerFrames?: number;
  durationInFrames: number;
}> = ({
  steps,
  accentColor = "#D97757",
  staggerFrames = 10,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Colors ────────────────────────────────────────────────────────────────
  const COLOR_TEXT = "#FFFFFF";
  const COLOR_SUBLABEL = "rgba(255,255,255,0.60)";
  const COLOR_CIRCLE_BG = "rgba(255,255,255,0.10)";
  const BG_COLOR = "rgba(0,0,0,0.70)";
  const FONT_FAMILY = "'Inter', system-ui, sans-serif";

  // ── Layout ────────────────────────────────────────────────────────────────
  const CIRCLE_SIZE = 52;
  const LINE_X = CIRCLE_SIZE / 2;
  const STEP_HEIGHT = 96;

  // ── Timing ────────────────────────────────────────────────────────────────
  const ENTER_FRAMES = 5;
  const EXIT_START = Math.max(0, durationInFrames - 5);

  // ── Container opacity ─────────────────────────────────────────────────────
  const entryOpacity = interpolate(frame, [0, ENTER_FRAMES], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(
    frame,
    [EXIT_START, Math.max(EXIT_START + 1, durationInFrames)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const combinedOpacity = entryOpacity * exitOpacity;

  // ── Connecting line height: grows as steps appear ─────────────────────────
  // Line starts when step 1 appears and extends to the last completed step
  const totalLineHeight = (steps.length - 1) * STEP_HEIGHT;
  const lineRevealFrame = (steps.length - 1) * staggerFrames + 15;
  const lineProgress = interpolate(frame, [staggerFrames, lineRevealFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const lineHeight = lineProgress * totalLineHeight;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: combinedOpacity,
      }}
    >
      <div
        style={{
          background: BG_COLOR,
          borderRadius: 24,
          padding: "36px 44px 36px 36px",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.10)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
          position: "relative",
          minWidth: 440,
          maxWidth: 680,
        }}
      >
        {/* ── Vertical connecting line ──────────────────────────────────────── */}
        <div
          style={{
            position: "absolute",
            left: 36 + LINE_X,
            top: 36 + CIRCLE_SIZE,
            width: 2,
            height: lineHeight,
            background: `linear-gradient(to bottom, ${accentColor}BB, ${accentColor}33)`,
            borderRadius: 1,
            overflow: "hidden",
          }}
        />

        {/* ── Steps ──────────────────────────────────────────────────────────── */}
        {steps.map((step, i) => {
          const stepSpring = spring({
            frame: frame - i * staggerFrames,
            fps,
            config: { damping: 14, stiffness: 220, mass: 0.7 },
          });
          const stepOpacity = interpolate(stepSpring, [0, 1], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const stepTranslate = interpolate(stepSpring, [0, 1], [18, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const stepScale = interpolate(stepSpring, [0, 1], [0.88, 1.0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          const circleColor = step.color ?? accentColor;
          const isActive = frame >= i * staggerFrames + 8;

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 18,
                marginBottom: i < steps.length - 1 ? STEP_HEIGHT - CIRCLE_SIZE : 0,
                opacity: stepOpacity,
                transform: `translateX(${stepTranslate}px) scale(${stepScale})`,
              }}
            >
              {/* ── Circle badge ─────────────────────────────────────────── */}
              <div
                style={{
                  width: CIRCLE_SIZE,
                  height: CIRCLE_SIZE,
                  borderRadius: "50%",
                  background: isActive ? circleColor : COLOR_CIRCLE_BG,
                  border: `2px solid ${isActive ? circleColor : "rgba(255,255,255,0.2)"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  boxShadow: isActive ? `0 0 20px ${circleColor}55` : "none",
                  transition: "background 0.1s",
                }}
              >
                <span
                  style={{
                    fontSize: 22,
                    fontWeight: 800,
                    color: isActive ? "#FFFFFF" : "rgba(255,255,255,0.4)",
                    fontFamily: FONT_FAMILY,
                    lineHeight: 1,
                  }}
                >
                  {i + 1}
                </span>
              </div>

              {/* ── Text ─────────────────────────────────────────────────── */}
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <span
                  style={{
                    fontSize: 30,
                    fontWeight: 700,
                    color: isActive ? COLOR_TEXT : "rgba(255,255,255,0.45)",
                    fontFamily: FONT_FAMILY,
                    letterSpacing: -0.3,
                    lineHeight: 1.2,
                  }}
                >
                  {step.label}
                </span>
                {step.sublabel && (
                  <span
                    style={{
                      fontSize: 22,
                      fontWeight: 400,
                      color: COLOR_SUBLABEL,
                      fontFamily: FONT_FAMILY,
                    }}
                  >
                    {step.sublabel}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
