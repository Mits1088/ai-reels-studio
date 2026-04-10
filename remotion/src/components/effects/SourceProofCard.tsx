import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
  Img,
  staticFile,
} from "remotion";

/**
 * SourceProofCard — Designed dark card displaying a social media post as trust proof.
 * Inspired by thevarunmayya's styled tweet cards — editorial, not a raw screenshot.
 *
 * Frame-driven animation: spring entrance, highlight scanning, staggered numbered points.
 */

interface NumberedPoint {
  number: number;
  text: string;
}

interface SourceProofCardProps {
  authorName: string;
  authorHandle: string;
  authorAvatar?: string;
  verified?: boolean;
  bodyText: string;
  highlightPhrases?: string[];
  highlightColor?: string;
  numberedPoints?: NumberedPoint[];
  durationInFrames: number;
  platform?: "twitter" | "threads" | "generic";
}

const POINT_COLORS = ["#4285F4", "#EA4335", "#34A853", "#FBBC05", "#8E24AA", "#00ACC1"];

const VerifiedBadge: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
    <circle cx="12" cy="12" r="10" fill="#1DA1F2" />
    <path
      d="M9.5 12.5L11 14L15 10"
      stroke="#FFFFFF"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const PlatformIcon: React.FC<{ platform: string }> = ({ platform }) => {
  if (platform === "twitter") {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="#8899A6">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    );
  }
  if (platform === "threads") {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="#8899A6">
        <path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017C1.5 8.418 2.35 5.564 3.995 3.512 5.845 1.207 8.598.025 12.179.002h.014c2.746.015 5.109.807 7.022 2.349.868.698 1.62 1.538 2.239 2.5l-1.7 1.163c-1.38-2.146-3.634-3.283-6.548-3.305-2.917.02-5.074.946-6.403 2.749C5.597 7.108 4.88 9.35 4.86 12c.02 2.65.737 4.892 1.943 6.541 1.33 1.804 3.486 2.73 6.403 2.75 2.238-.015 4.08-.601 5.404-1.732 1.5-1.282 2.204-3.15 2.108-5.074-.038-.766-.196-1.455-.456-2.056-.277-.643-.67-1.167-1.158-1.567a4.957 4.957 0 00-1.68-.91 5.873 5.873 0 00-.546-.168c.043.355.066.72.066 1.092 0 1.655-.424 3.18-1.2 4.394-1.097 1.717-2.87 2.727-4.88 2.78h-.086c-1.6-.043-3.07-.72-4.14-1.91-1.05-1.163-1.61-2.713-1.61-4.486 0-1.773.56-3.323 1.61-4.486 1.07-1.19 2.54-1.867 4.14-1.91h.085c1.227.033 2.364.412 3.364 1.117l-.99 1.48c-.69-.485-1.49-.76-2.37-.789h-.057c-1.076.029-2.03.489-2.76 1.3-.74.822-1.14 1.919-1.14 3.288s.4 2.466 1.14 3.288c.73.811 1.684 1.271 2.76 1.3h.057c1.198-.032 2.19-.597 2.87-1.663.48-.752.74-1.654.78-2.632a4.584 4.584 0 00-.012-.49 3.33 3.33 0 00-.65-.087c-.628 0-1.19.113-1.67.335l-.808-1.534c.82-.38 1.73-.573 2.694-.573.148 0 .296.005.443.016a6.87 6.87 0 012.552.752 5.408 5.408 0 011.88 1.355c.613.675 1.074 1.472 1.36 2.377.31.975.475 2.027.475 3.137v.017c.1 2.455-.818 4.812-2.664 6.39C17.834 23.146 15.328 23.98 12.186 24z" />
      </svg>
    );
  }
  return null;
};

/**
 * Renders body text with highlight scanning animation on specified phrases.
 */
const HighlightedBody: React.FC<{
  text: string;
  phrases: string[];
  color: string;
  frame: number;
  fps: number;
}> = ({ text, phrases, color, frame, fps }) => {
  if (phrases.length === 0) {
    return <span>{text}</span>;
  }

  // Build segments: split text around highlight phrases
  const segments: Array<{ text: string; isHighlight: boolean; index: number }> = [];
  let remaining = text;
  let highlightIdx = 0;

  // Simple approach: find each phrase in order and split around them
  const phrasePositions: Array<{ phrase: string; start: number; end: number; idx: number }> = [];
  for (let i = 0; i < phrases.length; i++) {
    const pos = text.toLowerCase().indexOf(phrases[i].toLowerCase());
    if (pos !== -1) {
      phrasePositions.push({ phrase: phrases[i], start: pos, end: pos + phrases[i].length, idx: i });
    }
  }
  phrasePositions.sort((a, b) => a.start - b.start);

  let cursor = 0;
  for (const pp of phrasePositions) {
    if (pp.start > cursor) {
      segments.push({ text: text.slice(cursor, pp.start), isHighlight: false, index: -1 });
    }
    segments.push({ text: text.slice(pp.start, pp.end), isHighlight: true, index: pp.idx });
    cursor = pp.end;
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), isHighlight: false, index: -1 });
  }

  return (
    <span>
      {segments.map((seg, i) => {
        if (!seg.isHighlight) {
          return <span key={i}>{seg.text}</span>;
        }

        // Stagger highlight sweep: each phrase activates 20 frames apart
        const sweepStart = 12 + seg.index * 20;
        const sweepProgress = interpolate(
          frame,
          [sweepStart, sweepStart + 12],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        return (
          <span
            key={i}
            style={{
              position: "relative",
              display: "inline",
            }}
          >
            <span
              style={{
                position: "absolute",
                left: 0,
                top: -2,
                bottom: -2,
                width: `${sweepProgress * 100}%`,
                background: color,
                borderRadius: 4,
                zIndex: 0,
              }}
            />
            <span style={{ position: "relative", zIndex: 1 }}>{seg.text}</span>
          </span>
        );
      })}
    </span>
  );
};

export const SourceProofCard: React.FC<SourceProofCardProps> = ({
  authorName,
  authorHandle,
  authorAvatar,
  verified = false,
  bodyText,
  highlightPhrases = [],
  highlightColor = "rgba(66, 133, 244, 0.3)",
  numberedPoints = [],
  durationInFrames,
  platform = "generic",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Card entrance: spring scale + opacity
  const entranceSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 180, mass: 0.8 },
  });
  const cardScale = interpolate(entranceSpring, [0, 1], [0.9, 1]);
  const cardOpacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Exit fade
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 6, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Follow button slide-in
  const followSlide = spring({
    frame: Math.max(0, frame - 6),
    fps,
    config: { damping: 16, stiffness: 200, mass: 0.6 },
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          maxWidth: "90%",
          width: 920,
          background: "#1A1A1A",
          borderRadius: 20,
          padding: 28,
          transform: `scale(${cardScale})`,
          opacity: cardOpacity * exitOpacity,
          boxShadow: "0 20px 60px rgba(0,0,0,0.4)",
          fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        }}
      >
        {/* Author row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 20,
          }}
        >
          {/* Avatar */}
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              background: "#333333",
              overflow: "hidden",
              flexShrink: 0,
            }}
          >
            {authorAvatar ? (
              <Img
                src={
                  authorAvatar.startsWith("http")
                    ? authorAvatar
                    : staticFile(authorAvatar)
                }
                style={{ width: 40, height: 40, objectFit: "cover" }}
              />
            ) : (
              <div
                style={{
                  width: 40,
                  height: 40,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "#444444",
                  color: "#FFFFFF",
                  fontSize: 18,
                  fontWeight: 700,
                }}
              >
                {authorName.charAt(0)}
              </div>
            )}
          </div>

          {/* Name + handle */}
          <div style={{ display: "flex", flexDirection: "column", gap: 1, flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  color: "#FFFFFF",
                  fontSize: 16,
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                {authorName}
              </span>
              {verified && <VerifiedBadge />}
              <PlatformIcon platform={platform} />
            </div>
            <span
              style={{
                color: "#8899A6",
                fontSize: 14,
                lineHeight: 1.2,
              }}
            >
              {authorHandle}
            </span>
          </div>

          {/* Follow button */}
          <div
            style={{
              background: "#1DA1F2",
              color: "#FFFFFF",
              fontSize: 14,
              fontWeight: 700,
              padding: "8px 20px",
              borderRadius: 100,
              transform: `scale(${interpolate(followSlide, [0, 1], [0.7, 1])})`,
              opacity: followSlide,
              cursor: "default",
              whiteSpace: "nowrap",
            }}
          >
            Follow
          </div>
        </div>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: "rgba(255,255,255,0.08)",
            marginBottom: 20,
          }}
        />

        {/* Body text */}
        <div
          style={{
            color: "#FFFFFF",
            fontSize: 18,
            lineHeight: 1.5,
            padding: "0 4px",
            marginBottom: numberedPoints.length > 0 ? 20 : 0,
          }}
        >
          <HighlightedBody
            text={bodyText}
            phrases={highlightPhrases}
            color={highlightColor}
            frame={frame}
            fps={fps}
          />
        </div>

        {/* Numbered points */}
        {numberedPoints.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, padding: "0 4px" }}>
            {numberedPoints.map((point, idx) => {
              // Stagger entrance for each point
              const pointDelay = 8 + idx * 10;
              const pointSpring = spring({
                frame: Math.max(0, frame - pointDelay),
                fps,
                config: { damping: 14, stiffness: 200, mass: 0.7 },
              });
              const pointScale = interpolate(pointSpring, [0, 1], [0.8, 1]);
              const pointSlideX = interpolate(pointSpring, [0, 1], [20, 0]);
              const badgeColor = POINT_COLORS[idx % POINT_COLORS.length];

              return (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                    transform: `translateX(${pointSlideX}px) scale(${pointScale})`,
                    opacity: pointSpring,
                  }}
                >
                  {/* Number badge */}
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: badgeColor,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        color: "#FFFFFF",
                        fontSize: 17,
                        fontWeight: 800,
                        lineHeight: 1,
                        fontFamily: "system-ui, sans-serif",
                      }}
                    >
                      {point.number}
                    </span>
                  </div>

                  {/* Point text */}
                  <span
                    style={{
                      color: "#E0E0E0",
                      fontSize: 16,
                      fontWeight: 500,
                      lineHeight: 1.4,
                    }}
                  >
                    {point.text}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
