import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, Img, staticFile } from "remotion";

/**
 * LowerThird — Animated name/title card that slides in from the left.
 * Essential for professional reels — identifies speakers, topics, or sources.
 * Features an accent line, glassmorphism card, and staggered text reveal.
 */
export const LowerThird: React.FC<{
  title: string;
  subtitle?: string;
  accentColor?: string;
  durationInFrames: number;
  position?: "bottom-left" | "bottom-center" | "top-left";
  titleFontSize?: number;
  subtitleFontSize?: number;
  logoSrc?: string;
}> = ({
  title,
  subtitle,
  accentColor = "#00E5FF",
  durationInFrames,
  position = "bottom-left",
  titleFontSize = 30,
  subtitleFontSize = 20,
  logoSrc,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Accent line slides in first
  const lineEnter = spring({ frame, fps, config: { damping: 18, stiffness: 200 } });
  // Card slides in slightly after
  const cardEnter = spring({ frame: Math.max(0, frame - 3), fps, config: { damping: 16, stiffness: 160 } });
  // Subtitle fades in last
  const subtitleEnter = interpolate(frame, [8, 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Exit
  const exit = interpolate(frame, [durationInFrames - 5, durationInFrames], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const exitSlide = exit * 80;
  const exitOpacity = 1 - exit;

  const posStyle: React.CSSProperties =
    position === "bottom-center"
      ? { bottom: 200, left: "50%", transform: `translateX(-50%) translateX(${-exitSlide}px)` }
      : position === "top-left"
      ? { top: 100, left: 48, transform: `translateX(${-exitSlide}px)` }
      : { bottom: 200, left: 48, transform: `translateX(${-exitSlide}px)` };

  return (
    <div
      style={{
        position: "absolute",
        zIndex: 55,
        opacity: exitOpacity,
        ...posStyle,
      }}
    >
      {/* Accent line */}
      <div style={{
        width: interpolate(lineEnter, [0, 1], [0, 60]),
        height: 3,
        background: accentColor,
        borderRadius: 2,
        marginBottom: 10,
        boxShadow: `0 0 10px ${accentColor}40`,
      }} />

      {/* Card */}
      <div style={{
        background: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(8px)",
        borderRadius: 12,
        padding: "12px 24px",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        transform: `translateX(${interpolate(cardEnter, [0, 1], [-60, 0])}px)`,
        opacity: cardEnter,
        display: "flex",
        alignItems: "center",
        gap: logoSrc ? 16 : 0,
      }}>
        {logoSrc && (
          <Img
            src={staticFile(logoSrc)}
            style={{
              width: titleFontSize * 1.4,
              height: titleFontSize * 1.4,
              flexShrink: 0,
            }}
          />
        )}
        <div>
          <div style={{
            fontSize: titleFontSize,
            fontWeight: 700,
            color: "#FFFFFF",
            fontFamily: "'Inter', 'Segoe UI', sans-serif",
            letterSpacing: "-0.01em",
          }}>
            {title}
          </div>
          {subtitle && (
            <div style={{
              fontSize: subtitleFontSize,
              fontWeight: 400,
              color: "rgba(255, 255, 255, 0.55)",
              marginTop: 2,
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
              opacity: subtitleEnter,
            }}>
              {subtitle}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
