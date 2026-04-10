import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

// ────────────────────────────────────────────────────────────────
// SkillActivationScene — beat-08 (28.60–33.74s, ~154 frames)
//
// The reel's biggest payoff moment. Shows Claude auto-activating
// the Social Media Writer skill without being asked. Premium
// dark-pill + spring-badge reveal with pulsing ring.
// ────────────────────────────────────────────────────────────────

const NOTIF_IN    = 8;    // notification bar slides down
const BADGE_IN    = 32;   // skill badge pops in
const LABEL_IN    = 52;   // skill name + active status
const BANNER_IN   = 72;   // auto-activated dark banner
const PULSE_START = 58;   // ring pulse begins
const SUPPORT_IN  = 108;  // supporting copy fades in
const FADE_OUT    = 140;  // global fade-out start

export const SkillActivationScene: React.FC<{ durationInFrames: number }> = ({
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Global fade-out
  const globalOpacity = interpolate(
    frame,
    [FADE_OUT, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Notification bar from top
  const notifProg = spring({
    frame: Math.max(0, frame - NOTIF_IN),
    fps,
    config: { damping: 18, stiffness: 160, mass: 0.88 },
  });

  // Skill badge pop
  const badgeProg = spring({
    frame: Math.max(0, frame - BADGE_IN),
    fps,
    config: { damping: 12, stiffness: 250, mass: 0.65 },
  });

  // Name + status
  const labelProg = spring({
    frame: Math.max(0, frame - LABEL_IN),
    fps,
    config: { damping: 200, stiffness: 120 },
  });

  // AUTO-ACTIVATED banner
  const bannerProg = spring({
    frame: Math.max(0, frame - BANNER_IN),
    fps,
    config: { damping: 16, stiffness: 210, mass: 0.82 },
  });

  // Supporting copy
  const supportProg = spring({
    frame: Math.max(0, frame - SUPPORT_IN),
    fps,
    config: { damping: 200, stiffness: 100 },
  });

  // Pulse ring — only active after PULSE_START
  const pulseFrame = Math.max(0, frame - PULSE_START);
  const pulseCycle = pulseFrame % 44;
  const ringScale  =
    frame >= PULSE_START
      ? interpolate(pulseCycle, [0, 44], [1.0, 2.4], { extrapolateRight: "clamp" })
      : 1;
  const ringOpacity =
    frame >= PULSE_START
      ? interpolate(pulseCycle, [0, 14, 44], [0.7, 0.3, 0], { extrapolateRight: "clamp" })
      : 0;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: globalOpacity,
        zIndex: 30,
        pointerEvents: "none",
      }}
    >
      {/* ── Notification bar (slides down from top) ── */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          transform: `translateY(${interpolate(notifProg, [0, 1], [-110, 0])}px)`,
          background: "linear-gradient(90deg, #1C1917 0%, #2D1B14 55%, #1C1917 100%)",
          padding: "26px 52px",
          display: "flex",
          alignItems: "center",
          gap: 18,
          zIndex: 40,
          borderBottom: "1px solid rgba(204,120,92,0.22)",
        }}
      >
        {/* Live dot */}
        <div
          style={{
            width: 12,
            height: 12,
            borderRadius: "50%",
            background: "#CC785C",
            boxShadow: "0 0 10px #CC785C, 0 0 22px rgba(204,120,92,0.4)",
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: "#FAF9F7",
            fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            letterSpacing: 2.5,
            textTransform: "uppercase",
          }}
        >
          Skill Detected
        </span>
        <span
          style={{
            marginLeft: "auto",
            fontSize: 20,
            fontWeight: 700,
            color: "#CC785C",
            fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            letterSpacing: 1,
          }}
        >
          Claude Skills
        </span>
      </div>

      {/* ── Main content area ── */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 28,
          width: "100%",
          padding: "32px 64px 0",
          marginTop: 30,
        }}
      >
        {/* Skill badge + pulse ring */}
        <div
          style={{
            position: "relative",
            width: 152,
            height: 152,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {/* Expanding ring */}
          <div
            style={{
              position: "absolute",
              width: 132,
              height: 132,
              borderRadius: "50%",
              border: "3px solid #CC785C",
              transform: `scale(${ringScale})`,
              opacity: ringOpacity,
              pointerEvents: "none",
            }}
          />

          {/* Badge */}
          <div
            style={{
              width: 132,
              height: 132,
              borderRadius: 40,
              background:
                "linear-gradient(135deg, #CC785C 0%, #E8B88A 52%, #F5C89A 100%)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
              transform: `scale(${interpolate(badgeProg, [0, 1], [0.15, 1])})`,
              opacity: interpolate(badgeProg, [0, 0.1], [0, 1]),
              boxShadow:
                "0 16px 52px rgba(204,120,92,0.42), 0 0 0 6px rgba(204,120,92,0.11)",
            }}
          >
            <span style={{ fontSize: 48, lineHeight: 1 }}>✍️</span>
            <span
              style={{
                fontSize: 13,
                fontWeight: 800,
                color: "rgba(255,255,255,0.95)",
                fontFamily:
                  "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                letterSpacing: 2.5,
                textTransform: "uppercase",
              }}
            >
              Skill
            </span>
          </div>
        </div>

        {/* Skill name + Active status */}
        <div
          style={{
            textAlign: "center",
            opacity: interpolate(labelProg, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(labelProg, [0, 1], [22, 0])}px)`,
          }}
        >
          <div
            style={{
              fontSize: 48,
              fontWeight: 900,
              color: "#1C1917",
              fontFamily:
                "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
              letterSpacing: -1.8,
              lineHeight: 1.02,
            }}
          >
            Social Media Writer
          </div>

          {/* Active pill */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              marginTop: 16,
              background: "rgba(204,120,92,0.09)",
              border: "1.5px solid rgba(204,120,92,0.28)",
              borderRadius: 50,
              padding: "10px 26px",
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#34A853",
                boxShadow: "0 0 8px rgba(52,168,83,0.85)",
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: "#CC785C",
                fontFamily:
                  "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
              }}
            >
              Active
            </span>
          </div>
        </div>

        {/* ── AUTO-ACTIVATED banner ── */}
        <div
          style={{
            width: "100%",
            transform: `translateY(${interpolate(bannerProg, [0, 1], [64, 0])}px) scale(${interpolate(bannerProg, [0, 1], [0.88, 1])})`,
            opacity: interpolate(bannerProg, [0, 0.1], [0, 1]),
            background:
              "linear-gradient(90deg, #1C1917 0%, #2D1B14 50%, #1C1917 100%)",
            borderRadius: 28,
            padding: "28px 36px",
            display: "flex",
            alignItems: "center",
            gap: 18,
            boxShadow:
              "0 10px 44px rgba(28,25,23,0.30), 0 0 0 1px rgba(204,120,92,0.16)",
          }}
        >
          <span style={{ fontSize: 38, lineHeight: 1, flexShrink: 0 }}>⚡</span>

          <div style={{ flex: 1 }}>
            <div
              style={{
                fontSize: 34,
                fontWeight: 900,
                color: "#FAF9F7",
                fontFamily:
                  "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                letterSpacing: 2,
                textTransform: "uppercase",
                lineHeight: 1,
              }}
            >
              Auto-Activated
            </div>
            <div
              style={{
                fontSize: 20,
                fontWeight: 600,
                color: "#E8B88A",
                fontFamily:
                  "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                marginTop: 7,
                letterSpacing: 0.2,
              }}
            >
              Claude applied it without being asked
            </div>
          </div>

          {/* Checkmark circle */}
          <div
            style={{
              width: 54,
              height: 54,
              borderRadius: "50%",
              background: "rgba(204,120,92,0.14)",
              border: "2px solid rgba(204,120,92,0.38)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontSize: 26,
                color: "#CC785C",
                fontWeight: 900,
                fontFamily:
                  "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
              }}
            >
              ✓
            </span>
          </div>
        </div>

        {/* Supporting copy */}
        <div
          style={{
            opacity: interpolate(supportProg, [0, 1], [0, 0.62]),
            textAlign: "center",
            fontSize: 23,
            fontWeight: 600,
            color: "#6B5A52",
            fontFamily:
              "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            letterSpacing: 0.15,
          }}
        >
          No setup needed every session
        </div>
      </div>
    </AbsoluteFill>
  );
};
