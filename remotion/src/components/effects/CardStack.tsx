import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

/**
 * CardStack — Staggered card reveal for lists, features, or multi-item scenes.
 * Cards slide in one-by-one from the side with a spring bounce.
 *
 * Props:
 * - items: array of { title, subtitle?, icon?, number? }
 * - staggerFrames: delay between each card
 * - direction: "left" | "right" — which side cards enter from
 * - cardColor: background color
 * - accentColor: border/icon color
 * - variant: "cinematic" (default dark translucent) or "editorial" (light, numbered, with rotation)
 */
export const CardStack: React.FC<{
  items: Array<{ title: string; subtitle?: string; icon?: string; number?: number }>;
  staggerFrames?: number;
  direction?: "left" | "right";
  cardColor?: string;
  accentColor?: string;
  durationInFrames: number;
  variant?: "cinematic" | "editorial";
}> = ({
  items,
  staggerFrames = 5,
  direction = "right",
  cardColor = "rgba(255, 255, 255, 0.06)",
  accentColor = "#00E5FF",
  durationInFrames,
  variant = "cinematic",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Exit fade
  const exitOpacity = interpolate(frame, [durationInFrames - 4, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        padding: "0 48px",
        width: "100%",
        opacity: exitOpacity,
      }}
    >
      {items.map((item, i) => {
        const delay = i * staggerFrames;
        const localFrame = Math.max(0, frame - delay);
        const springConfig = variant === "editorial"
          ? { damping: 12, stiffness: 160, mass: 0.7 }
          : { damping: 14, stiffness: 180 };
        const s = spring({ frame: localFrame, fps, config: springConfig });

        const slideFrom = direction === "right" ? (variant === "editorial" ? 400 : 200) : (variant === "editorial" ? -400 : -200);
        const translateX = interpolate(s, [0, 1], [slideFrom, 0]);
        const rotation = variant === "editorial" ? interpolate(s, [0, 1], [8, 0]) : 0;
        const opacity = s;

        const isEditorial = variant === "editorial";
        const cardBg = isEditorial ? "#FFFFFF" : cardColor;
        const textColor = isEditorial ? "#1A1A1A" : "#FFFFFF";
        const subtitleColor = isEditorial ? "rgba(0,0,0,0.5)" : "rgba(255,255,255,0.5)";

        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              padding: isEditorial ? "20px 28px" : "18px 28px",
              borderRadius: isEditorial ? 20 : 16,
              background: cardBg,
              ...(isEditorial ? {} : { backdropFilter: "blur(8px)" }),
              border: isEditorial
                ? "1px solid rgba(0,0,0,0.08)"
                : "1px solid rgba(255, 255, 255, 0.08)",
              borderLeft: isEditorial ? "none" : `3px solid ${accentColor}`,
              transform: `translateX(${translateX}px) rotate(${rotation}deg)`,
              opacity,
              boxShadow: isEditorial
                ? "0 6px 24px rgba(0,0,0,0.12)"
                : "0 4px 24px rgba(0, 0, 0, 0.3)",
              marginTop: isEditorial && i > 0 ? -8 : 0,
            }}
          >
            {/* Number badge (editorial) */}
            {isEditorial && item.number != null && (
              <div
                style={{
                  width: 44,
                  height: 44,
                  minWidth: 44,
                  borderRadius: 12,
                  backgroundColor: accentColor,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 22,
                  fontWeight: 900,
                  color: "#FFFFFF",
                  fontFamily: "'Inter', 'Segoe UI', sans-serif",
                }}
              >
                {item.number}
              </div>
            )}
            {item.icon && (
              <span style={{ fontSize: 36, lineHeight: 1 }}>{item.icon}</span>
            )}
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: isEditorial ? 28 : 30,
                  fontWeight: 700,
                  color: textColor,
                  fontFamily: "'Inter', 'Segoe UI', sans-serif",
                  lineHeight: 1.3,
                }}
              >
                {item.title}
              </div>
              {item.subtitle && (
                <div
                  style={{
                    fontSize: isEditorial ? 20 : 22,
                    fontWeight: 400,
                    color: subtitleColor,
                    marginTop: 4,
                    fontFamily: "'Inter', 'Segoe UI', sans-serif",
                  }}
                >
                  {item.subtitle}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
