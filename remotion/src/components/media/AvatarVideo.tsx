import React from "react";
import {
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import type { TimelineEntry } from "../../types";
import { FPS, toFrame, getAvatarLayout } from "../../utils";

/**
 * AvatarVideo — ONE persistent OffthreadVideo, never unmounts.
 * Layout changes only affect the container's CSS — the video element
 * stays alive across every transition, keeping audio continuous.
 */
export const AvatarVideo: React.FC<{
  entries: TimelineEntry[];
  hideRanges?: Array<{ start: number; end: number }>;
}> = ({ entries, hideRanges = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeSec = frame / FPS;

  // Hide avatar when center-full broll is active
  const isHiddenByBroll = hideRanges.some(
    (r) => currentTimeSec >= r.start && currentTimeSec < r.end
  );

  const result = getAvatarLayout(entries, currentTimeSec);
  const layout = isHiddenByBroll ? null : (result?.layout ?? null);
  const entry = result?.entry ?? null;

  const entryIndex = entry ? entries.indexOf(entry) : -1;
  const prevLayout = entryIndex > 0 ? (entries[entryIndex - 1]?.layout ?? "full-screen") : null;
  const nextLayout = entryIndex >= 0 && entryIndex < entries.length - 1
    ? (entries[entryIndex + 1]?.layout ?? "full-screen")
    : null;

  const localFrame = entry ? frame - toFrame(entry.start) : 0;
  const entryDuration = entry ? toFrame(entry.end) - toFrame(entry.start) : 1;

  const isEnterChange = layout !== null && prevLayout !== layout;

  // ── Layout detection (needed before opacity) ──
  const isSplit = layout === "split-screen";
  const isHookReveal = layout === "hook-reveal";
  const isFromFullScreen = isSplit && isEnterChange && prevLayout === "full-screen";

  // ── Hook-reveal: avatar starts full-screen, springs to bottom 62% at punchFrame ──
  const punchFrame = entry?.punchFrame ?? 15;
  const hookSplit = spring({
    frame: Math.max(0, localFrame - punchFrame),
    fps,
    config: { damping: 16, stiffness: 180, mass: 0.8 },
  });
  // Height springs from 100% → 62%, top springs from 0% → 38%
  const hookHeight = isHookReveal
    ? interpolate(hookSplit, [0, 1], [100, 62], { extrapolateRight: "clamp" })
    : 60;
  // Punch scale bump — peaks at punchFrame, settles back
  const punchBump = isHookReveal
    ? spring({ frame: Math.max(0, localFrame - punchFrame), fps,
        config: { damping: 6, stiffness: 500, mass: 0.5 } })
    : 1;
  const punchScale = isHookReveal
    ? interpolate(punchBump, [0, 0.25, 1], [1.0, 1.05, 1.0], { extrapolateRight: "clamp" })
    : 1;
  // Entrance zoom-in: 1.1 → 1.0 over first 12 frames
  const hookEnterScale = isHookReveal
    ? interpolate(localFrame, [0, 12], [1.1, 1.0], { extrapolateRight: "clamp" })
    : 1;

  // Opacity — skip fades when the slide animation handles the visual transition
  // (full-screen → split-screen: the slide-down IS the transition — no opacity needed on either side)
  let opacity = layout === null ? 0 : 1;

  // Fade in only for entries that aren't sliding in from full-screen or hook-reveal
  if (layout !== null && isEnterChange && !isFromFullScreen && !isHookReveal && localFrame < 6) {
    opacity = interpolate(localFrame, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  // Fade out only at true end of avatar (no next layout)
  if (layout !== null && nextLayout === null && localFrame > entryDuration - 7) {
    opacity = interpolate(localFrame, [entryDuration - 6, entryDuration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  // Full-screen subtle Ken Burns
  const fsScale = layout === "full-screen"
    ? interpolate(localFrame, [0, entryDuration], [1.0, 1.04], { extrapolateRight: "clamp" })
    : 1;
  const fsEnterScale = (layout === "full-screen" && isEnterChange)
    ? interpolate(localFrame, [0, 4, 8], [1.08, 0.99, 1.0], { extrapolateRight: "clamp" })
    : 1;

  // Split-screen slide-in spring
  // From full-screen: slow, smooth settle downward (stiffness 90)
  // Normal enter: fast slide up from below (stiffness 160)
  const slideIn = (isSplit && isEnterChange)
    ? spring({ frame: localFrame, fps, config: {
        damping: isFromFullScreen ? 18 : 14,
        stiffness: isFromFullScreen ? 90 : 160,
      }})
    : 1;

  // From full-screen: avatar slides DOWN 768px (40% of 1920) to reach split-screen top edge
  // Normal enter: slides UP 60px from below
  const slideY = isFromFullScreen
    ? interpolate(slideIn, [0, 1], [-768, 0])
    : interpolate(slideIn, [0, 1], [60, 0]);
  const isFullScreen = layout === "full-screen";
  const isHidden = layout === null;

  const containerStyle: React.CSSProperties = isHidden ? {
    position: "absolute",
    width: 0, height: 0,
    opacity: 0,
    overflow: "hidden",
    pointerEvents: "none",
  } : isHookReveal ? {
    position: "absolute",
    bottom: 0, left: 0, right: 0,
    height: `${hookHeight}%`,
    zIndex: 10,
    opacity,
    overflow: "hidden",
  } : isSplit ? {
    position: "absolute",
    bottom: 0, left: 0, right: 0,
    height: "60%",
    zIndex: 10,
    opacity,
    overflow: "hidden",
    transform: isEnterChange ? `translateY(${slideY}px)` : undefined,
  } : {
    // full-screen
    position: "absolute",
    inset: 0,
    zIndex: 5,
    opacity,
    overflow: "hidden",
  };

  const videoScale = isHookReveal
    ? `scale(${hookEnterScale * punchScale})`
    : isFullScreen
    ? `scale(${fsScale * fsEnterScale})`
    : undefined;

  return (
    <div style={containerStyle}>
      {/* Top accent line — split-screen and hook-reveal */}
      {(isSplit || isHookReveal) && (
        <>
          <div style={{
            position: "absolute",
            top: 0, left: 0, right: 0,
            height: 2,
            background: "linear-gradient(90deg, transparent, rgba(66,133,244,0.6) 50%, transparent)",
            zIndex: 2,
          }} />
          <div style={{
            position: "absolute",
            top: 0, left: 0, right: 0,
            height: 40,
            background: "linear-gradient(180deg, rgba(13,17,23,0.8) 0%, transparent 100%)",
            zIndex: 1,
          }} />
        </>
      )}

      {/* Single persistent OffthreadVideo — never remounts */}
      <div style={{
        width: "100%", height: "100%",
        transform: videoScale,
      }}>
        <OffthreadVideo
          src={staticFile(entries[0]?.asset ?? "avatar.mp4")}
          muted
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: (isSplit || isHookReveal) ? "center top" : "center",
          }}
        />
      </div>
    </div>
  );
};
