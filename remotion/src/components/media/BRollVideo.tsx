import React from "react";
import { useCurrentFrame, interpolate, OffthreadVideo, staticFile, spring, useVideoConfig } from "remotion";
import type { TimelineEntry } from "../../types";
import { getPreset } from "../transitions/presets";
import { TransitionWrapper } from "../transitions/TransitionWrapper";
import { GlowBorder } from "../effects/GlowBorder";
import { PunchInZoom } from "../effects/PunchInZoom";

export const BRollVideo: React.FC<{
  src: string;
  durationInFrames: number;
  splitScreen?: boolean;
  entry?: TimelineEntry;
}> = ({ src, durationInFrames, splitScreen, entry }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const preset = getPreset(entry);
  const display = entry?.display;

  const zoomMoments = entry?.zoom_moments;
  const playbackRate = entry?.playbackRate ?? 1;
  const clipStartFrame = entry?.clipStartTime != null ? Math.round(entry.clipStartTime * fps) : 0;

  // Guard against short clips where durationInFrames - 15 < 15
  const fadeIn = Math.min(15, Math.floor(durationInFrames * 0.3));
  const fadeOut = Math.max(fadeIn + 1, durationInFrames - fadeIn);
  const glowIntensity = interpolate(
    frame,
    [0, fadeIn, fadeOut, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const videoElement = (
    <OffthreadVideo
      src={staticFile(src)}
      muted
      playbackRate={playbackRate}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: "center",
      }}
    />
  );

  const videoWithZoom = zoomMoments && zoomMoments.length > 0
    ? <PunchInZoom moments={zoomMoments}>{videoElement}</PunchInZoom>
    : videoElement;

  // ── center-full: full-frame video, fully visible ──
  if (display === "center-full") {
    return (
      <div style={{ position: "absolute", inset: 0, zIndex: 12, overflow: "hidden" }}>
        <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
          <OffthreadVideo
            src={staticFile(src)}
            muted
            playbackRate={playbackRate}
            startFrom={clipStartFrame}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        </TransitionWrapper>
      </div>
    );
  }

  // ── bg: full-screen behind avatar — demo video as background layer ──
  if (display === "bg") {
    return (
      <div style={{
        position: "absolute", inset: 0,
        zIndex: 4,
        overflow: "hidden",
      }}>
        <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
          <OffthreadVideo
            src={staticFile(src)}
            muted
            playbackRate={playbackRate}
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
          />
        </TransitionWrapper>
      </div>
    );
  }

  // ── responsive: fills top 40%, flush with avatar below ──
  if (display === "responsive") {
    return (
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        height: "40%",
        overflow: "hidden",
        zIndex: 10,
      }}>
        <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
          <OffthreadVideo
            src={staticFile(src)}
            muted
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: "center",
              display: "block",
            }}
          />
        </TransitionWrapper>
      </div>
    );
  }

  // ── hook-reveal: panel slides down from above at punchFrame, occupies top 38% ──
  if (display === "hook-reveal") {
    const punchFrame = entry?.punchFrame ?? 15;
    const slideIn = spring({
      frame: Math.max(0, frame - punchFrame),
      fps,
      config: { damping: 16, stiffness: 180, mass: 0.8 },
    });
    const translateY = interpolate(slideIn, [0, 1], [-100, 0], { extrapolateRight: "clamp" });
    return (
      <div style={{
        position: "absolute",
        top: 0, left: 0, right: 0,
        height: "38%",
        overflow: "hidden",
        zIndex: 11,
        transform: `translateY(${translateY}%)`,
      }}>
        <OffthreadVideo
          src={staticFile(src)}
          muted
          playbackRate={playbackRate}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
        />
      </div>
    );
  }

  // ── default split-screen / full-screen ──
  const containerStyle: React.CSSProperties = splitScreen
    ? { position: "absolute", top: 0, left: 0, right: 0, height: "40%", overflow: "hidden" }
    : { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 };

  return (
    <div style={containerStyle}>
      <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
            padding: splitScreen ? "8px 12px" : "20px 16px",
          }}
        >
          <div style={{ width: "100%", aspectRatio: "16/9", maxHeight: "100%" }}>
            <GlowBorder color="#00E5FF" borderRadius={16} intensity={glowIntensity}>
              {videoWithZoom}
            </GlowBorder>
          </div>
        </div>
      </TransitionWrapper>
    </div>
  );
};
