import React from "react";
import {
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
  Img,
  staticFile,
} from "remotion";

/**
 * StrikethroughSwap — Before/after transformation effect.
 *
 * Shows an old value with a red strikethrough line drawn across it,
 * then slides in a new value card from the right.
 * Inspired by thevarunmayya's email username change animation.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const StrikethroughSwap: React.FC<{
  oldValue: string;
  newValue: string;
  durationInFrames: number;
  strikethroughColor?: string;
  strikethroughDelay?: number;
  newValueDelay?: number;
  textColor?: string;
  fontSize?: number;
  newValueAvatar?: string;
  withCard?: boolean;
}> = ({
  oldValue,
  newValue,
  durationInFrames,
  strikethroughColor = "#DC2626",
  strikethroughDelay = 10,
  newValueDelay = 25,
  textColor = "#000",
  fontSize = 26,
  newValueAvatar,
  withCard = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Phase timing ──
  const strikethroughStart = strikethroughDelay;
  const strikethroughEnd = strikethroughStart + 12;
  const fadeStart = strikethroughEnd;
  const slideStart = newValueDelay;
  const slideEnd = slideStart + 15;

  // ── 1. Old value opacity ──
  const oldValueOpacity = interpolate(
    frame,
    [fadeStart, Math.max(fadeStart + 1, newValueDelay)],
    [1, 0.3],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // ── 2. Old value vertical shift (moves up 20px as it fades) ──
  const oldValueY = interpolate(
    frame,
    [fadeStart, Math.max(fadeStart + 1, newValueDelay)],
    [0, -20],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // ── 3. Strikethrough draw progress (0 → 1 via clipPath width) ──
  const strikethroughProgress = interpolate(
    frame,
    [strikethroughStart, strikethroughEnd],
    [0, 100],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // ── 4. New value card spring slide-in ──
  const cardSpring = spring({
    frame: Math.max(0, frame - slideStart),
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const cardTranslateX = interpolate(cardSpring, [0, 1], [300, 0]);
  const cardOpacity = interpolate(
    frame,
    [slideStart, slideStart + 5],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Card is only visible after newValueDelay
  const showCard = frame >= slideStart;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 32,
        fontFamily: "'Inter', 'system-ui', sans-serif",
      }}
    >
      {/* Old value with strikethrough */}
      <div
        style={{
          position: "relative",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: oldValueOpacity,
          transform: `translateY(${oldValueY}px)`,
        }}
      >
        {/* Old value text */}
        <span
          style={{
            fontSize,
            fontWeight: 500,
            color: textColor,
            letterSpacing: -0.3,
            whiteSpace: "nowrap",
          }}
        >
          {oldValue}
        </span>

        {/* Strikethrough line — drawn left to right via clipPath */}
        {frame >= strikethroughStart && (
          <div
            style={{
              position: "absolute",
              left: -4,
              right: -4,
              top: "50%",
              height: 3,
              backgroundColor: strikethroughColor,
              borderRadius: 2,
              transform: "translateY(-50%)",
              clipPath: `inset(0 ${100 - strikethroughProgress}% 0 0)`,
            }}
          />
        )}
      </div>

      {/* New value card */}
      {showCard && (
        <div
          style={{
            opacity: cardOpacity,
            transform: `translateX(${cardTranslateX}px)`,
            width: "85%",
            maxWidth: 600,
            ...(withCard
              ? {
                  background: "#FFFFFF",
                  borderRadius: 999,
                  boxShadow: "0 8px 32px rgba(0,0,0,0.1)",
                  padding: "12px 20px 12px 14px",
                }
              : {}),
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          {/* Avatar circle */}
          {newValueAvatar && (
            <div
              style={{
                width: 40,
                height: 40,
                minWidth: 40,
                borderRadius: "50%",
                overflow: "hidden",
                backgroundColor: "#E5E7EB",
              }}
            >
              <Img
                src={staticFile(newValueAvatar)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            </div>
          )}

          {/* Colored avatar placeholder when no image */}
          {!newValueAvatar && withCard && (
            <div
              style={{
                width: 40,
                height: 40,
                minWidth: 40,
                borderRadius: "50%",
                background:
                  "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)",
              }}
            />
          )}

          {/* New value text */}
          <span
            style={{
              flex: 1,
              fontSize: fontSize * 0.92,
              fontWeight: 600,
              color: textColor,
              letterSpacing: -0.3,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {newValue}
          </span>

          {/* Decorative close icon */}
          {withCard && (
            <div
              style={{
                width: 24,
                height: 24,
                minWidth: 24,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                opacity: 0.3,
              }}
            >
              <svg
                width={14}
                height={14}
                viewBox="0 0 14 14"
                fill="none"
                stroke={textColor}
                strokeWidth={1.8}
                strokeLinecap="round"
              >
                <line x1="1" y1="1" x2="13" y2="13" />
                <line x1="13" y1="1" x2="1" y2="13" />
              </svg>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
