import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

// ────────────────────────────────────────────────────────────────
// SkillQuestionsScene — beat-05 (13.54–18.64s, ~153 frames)
//
// Full-screen motion graphic showing the 4 clarifying questions
// Claude asks when building a skill. Cards spring in from right,
// one by one, with a staggered entrance.
// ────────────────────────────────────────────────────────────────

const QUESTIONS = [
  { text: "What kind of content do you create?",    icon: "✍️" },
  { text: "Who is your target audience?",            icon: "🎯" },
  { text: "What tone and style should I use?",       icon: "💬" },
  { text: "Can you share an example of your work?",  icon: "✨" },
];

const HEADER_IN  = 4;   // frame — header entrance
const CARD_FIRST = 18;  // frame — first card entrance
const CARD_GAP   = 22;  // frames between each card entrance
const FADE_OUT   = 140; // frame — start of global fade-out

export const SkillQuestionsScene: React.FC<{ durationInFrames: number }> = ({
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Global fade-out near the end
  const globalOpacity = interpolate(
    frame,
    [FADE_OUT, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Header entrance spring
  const headerProg = spring({
    frame: Math.max(0, frame - HEADER_IN),
    fps,
    config: { damping: 200, stiffness: 160, mass: 1 },
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 52px",
        opacity: globalOpacity,
        zIndex: 30,
      }}
    >
      {/* ── Header ── */}
      <div
        style={{
          width: "100%",
          opacity: interpolate(headerProg, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(headerProg, [0, 1], [-30, 0])}px)`,
          marginBottom: 44,
        }}
      >
        {/* Label row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 18,
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 15,
              background: "linear-gradient(135deg, #CC785C 0%, #E8B88A 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              boxShadow: "0 6px 18px rgba(204,120,92,0.38)",
              fontSize: 26,
            }}
          >
            🤖
          </div>
          <span
            style={{
              fontSize: 26,
              fontWeight: 700,
              color: "#CC785C",
              fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
              letterSpacing: 2.5,
              textTransform: "uppercase",
            }}
          >
            Claude asks you
          </span>
        </div>

        {/* Big number title */}
        <div
          style={{
            fontSize: 88,
            fontWeight: 900,
            color: "#1C1917",
            fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            letterSpacing: -4,
            lineHeight: 0.92,
          }}
        >
          4 Questions
        </div>

        {/* Accent underline */}
        <div
          style={{
            width: 80,
            height: 5,
            borderRadius: 3,
            background: "linear-gradient(90deg, #CC785C, #E8B88A)",
            marginTop: 20,
          }}
        />
      </div>

      {/* ── Question cards ── */}
      <div
        style={{
          width: "100%",
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        {QUESTIONS.map((q, i) => {
          const cardStart = CARD_FIRST + i * CARD_GAP;
          const cardProg  = spring({
            frame: Math.max(0, frame - cardStart),
            fps,
            config: { damping: 18, stiffness: 230, mass: 0.72 },
          });

          const xShift = interpolate(cardProg, [0, 1], [360, 0]);
          const opac   = interpolate(cardProg, [0, 0.07], [0, 1]);

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 22,
                background: "rgba(255,255,255,0.92)",
                borderRadius: 22,
                padding: "22px 26px 22px 26px",
                transform: `translateX(${xShift}px)`,
                opacity: opac,
                boxShadow:
                  "0 4px 28px rgba(204,120,92,0.11), 0 1px 4px rgba(0,0,0,0.07)",
                borderLeft: "5px solid #CC785C",
              }}
            >
              {/* Number badge */}
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background:
                    "linear-gradient(135deg, #CC785C 0%, #E8B88A 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  boxShadow: "0 4px 16px rgba(204,120,92,0.32)",
                }}
              >
                <span
                  style={{
                    fontSize: 26,
                    fontWeight: 900,
                    color: "#fff",
                    fontFamily:
                      "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                  }}
                >
                  {i + 1}
                </span>
              </div>

              {/* Question text */}
              <span
                style={{
                  fontSize: 28,
                  fontWeight: 700,
                  color: "#1C1917",
                  fontFamily:
                    "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                  lineHeight: 1.32,
                  letterSpacing: -0.4,
                  flex: 1,
                }}
              >
                {q.text}
              </span>

              {/* Icon */}
              <span
                style={{ fontSize: 30, flexShrink: 0, lineHeight: 1 }}
              >
                {q.icon}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
