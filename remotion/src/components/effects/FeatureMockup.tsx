import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

/**
 * FeatureMockup — Small card visualizing a single product feature.
 *
 * Takes an inline SVG path (24x24 viewBox) + a label + an optional list
 * of micro detail items. Renders as a clean dark card with the icon at
 * top, label below, optional details list, and a subtle scale-pop entry.
 *
 * Designed to layer ON TOP of cinematic b-roll (translucent dark backdrop)
 * during pain-elimination beats. Each feature gets its own visual mockup
 * instead of plain text strikethrough.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const FeatureMockup: React.FC<{
  label: string;
  durationInFrames: number;
  /** Inline SVG path data (24x24 viewBox assumed). */
  iconPath: string;
  /** Optional second icon path for multi-stroke icons (e.g. line + circle). */
  iconPath2?: string;
  /** Bullet items shown below the label as the "feature in action". */
  details?: string[];
  accentColor?: string;
  cardBackground?: string;
  textColor?: string;
  /** Vertical position of the card. */
  position?: "center" | "center-top" | "center-bottom";
  paddingY?: number;
}> = ({
  label,
  durationInFrames,
  iconPath,
  iconPath2,
  details = [],
  accentColor = "#D97757",
  cardBackground = "rgba(20, 20, 24, 0.92)",
  textColor = "#FFFFFF",
  position = "center",
  paddingY = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Spring scale-pop entry ──
  const cardSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 220, mass: 0.7 },
  });
  const cardScale = interpolate(cardSpring, [0, 1], [0.85, 1.0]);
  const cardOpacity = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Icon scale settle (slightly delayed) ──
  const iconSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 12, stiffness: 250, mass: 0.6 },
  });
  const iconScale = interpolate(iconSpring, [0, 1], [0.6, 1.0]);

  // ── Detail items stagger in ──
  const detailOpacity = (i: number) =>
    interpolate(frame, [10 + i * 4, 14 + i * 4], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  const detailY = (i: number) =>
    interpolate(frame, [10 + i * 4, 16 + i * 4], [12, 0], {
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

  const justifyContent =
    position === "center-top"
      ? "flex-start"
      : position === "center-bottom"
        ? "flex-end"
        : "center";

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent,
        paddingTop: position === "center-top" ? paddingY : 0,
        paddingBottom: position === "center-bottom" ? paddingY : 0,
        zIndex: 30,
        opacity: cardOpacity * exitOpacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: cardBackground,
          padding: details.length > 0 ? "44px 56px 36px" : "52px 64px",
          borderRadius: 36,
          boxShadow:
            "0 24px 80px rgba(0, 0, 0, 0.55), 0 4px 16px rgba(0, 0, 0, 0.4)",
          border: `1.5px solid ${accentColor}40`,
          transform: `scale(${cardScale})`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          maxWidth: 760,
          minWidth: 560,
        }}
      >
        {/* Icon */}
        <div
          style={{
            width: 144,
            height: 144,
            borderRadius: 28,
            background: `${accentColor}1A`,
            border: `2px solid ${accentColor}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${iconScale})`,
            marginBottom: 28,
          }}
        >
          <svg
            width="84"
            height="84"
            viewBox="0 0 24 24"
            fill="none"
            stroke={accentColor}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d={iconPath} />
            {iconPath2 && <path d={iconPath2} />}
          </svg>
        </div>

        {/* Label */}
        <div
          style={{
            fontSize: 56,
            fontWeight: 800,
            color: textColor,
            fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
            letterSpacing: -1,
            textAlign: "center",
            lineHeight: 1.1,
          }}
        >
          {label}
        </div>

        {/* Details list (optional) */}
        {details.length > 0 && (
          <div style={{ marginTop: 24, width: "100%" }}>
            {details.map((d, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "10px 0",
                  fontSize: 26,
                  fontWeight: 500,
                  color: `${textColor}D9`,
                  fontFamily:
                    "'Inter', system-ui, -apple-system, sans-serif",
                  opacity: detailOpacity(i),
                  transform: `translateY(${detailY(i)}px)`,
                  borderTop: i === 0 ? `1px solid ${textColor}1A` : "none",
                }}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    backgroundColor: accentColor,
                    flexShrink: 0,
                    marginTop: i === 0 ? 14 : 0,
                  }}
                />
                <span style={{ marginTop: i === 0 ? 14 : 0 }}>{d}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
