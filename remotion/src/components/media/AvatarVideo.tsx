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
import { FPS, toFrame, getAvatarLayout, SPLIT_HEIGHT_PCT } from "../../utils";

/**
 * AvatarVideo — ONE persistent OffthreadVideo, never unmounts.
 * Layout changes only affect the container's CSS — the video element
 * stays alive across every transition, keeping audio continuous.
 */
export const AvatarVideo: React.FC<{
  entries: TimelineEntry[];
  hideRanges?: Array<{ start: number; end: number }>;
}> = ({ entries, hideRanges = [] }) => {
  // ── Layout constants ────────────────────────────────────────────────────────
  // SPLIT_HEIGHT_PCT comes from utils.ts — DO NOT redefine here.
  // Content containers must use CONTENT_HEIGHT_PCT from utils.ts to match.
  const HOOK_REVEAL_HEIGHT_PCT = 62;        // hook-reveal settled height (slightly taller than split)
  const FULL_TO_SPLIT_SLIDE_PX = 768;       // 40% × 1920px — slide dist for full-screen → split
  const SPLIT_ENTER_SLIDE_FROM_PX = 60;     // normal split enter: slides up from this far below
  const ACCENT_LINE_HEIGHT_PX = 2;          // top accent line thickness in split-screen
  const ACCENT_GRADIENT_HEIGHT_PX = 40;     // top dark gradient height in split-screen
  // ── Timing constants ───────────────────────────────────────────────────────
  const HOOK_PUNCH_FRAME_DEFAULT = 15;      // default frame when hook-reveal punch fires
  const OPACITY_ENTER_FRAMES = 6;           // fade-in duration for normal enter transitions
  const OPACITY_EXIT_FRAMES = 6;            // fade-out duration at end of last avatar entry
  const FS_ENTER_SETTLE_FRAMES = [0, 4, 8]; // full-screen enter bounce keyframes
  const HOOK_ENTER_SCALE_FRAMES = 12;       // hook-reveal enter zoom duration
  // ── Animation constants ─────────────────────────────────────────────────────
  const FS_KENBURNS_MAX = 1.04;             // full-screen Ken Burns max scale drift
  const FS_ENTER_SCALE = 1.08;              // full-screen enter overshoot scale peak
  // ────────────────────────────────────────────────────────────────────────────
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
  const punchFrame = entry?.punchFrame ?? HOOK_PUNCH_FRAME_DEFAULT;
  const hookSplit = spring({
    frame: Math.max(0, localFrame - punchFrame),
    fps,
    config: { damping: 16, stiffness: 180, mass: 0.8 },
  });
  // Height springs from 100% → 62%, top springs from 0% → 38%
  const hookHeight = isHookReveal
    ? interpolate(hookSplit, [0, 1], [100, HOOK_REVEAL_HEIGHT_PCT], { extrapolateRight: "clamp" })
    : SPLIT_HEIGHT_PCT;
  // Punch scale bump — peaks at punchFrame, settles back
  const punchBump = isHookReveal
    ? spring({ frame: Math.max(0, localFrame - punchFrame), fps,
        config: { damping: 6, stiffness: 500, mass: 0.5 } })
    : 1;
  const punchScale = isHookReveal
    ? interpolate(punchBump, [0, 0.25, 1], [1.0, 1.05, 1.0], { extrapolateRight: "clamp" })
    : 1;
  // Entrance zoom-in: 1.1 → 1.0 over first HOOK_ENTER_SCALE_FRAMES frames
  const hookEnterScale = isHookReveal
    ? interpolate(localFrame, [0, HOOK_ENTER_SCALE_FRAMES], [1.1, 1.0], { extrapolateRight: "clamp" })
    : 1;

  // Opacity — skip fades when the slide animation handles the visual transition
  // (full-screen → split-screen: the slide-down IS the transition — no opacity needed on either side)
  let opacity = layout === null ? 0 : 1;

  // Fade in only for entries that aren't sliding in from full-screen or hook-reveal
  if (layout !== null && isEnterChange && !isFromFullScreen && !isHookReveal && localFrame < OPACITY_ENTER_FRAMES) {
    opacity = interpolate(localFrame, [0, OPACITY_ENTER_FRAMES], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  // Fade out only at true end of avatar (no next layout)
  if (layout !== null && nextLayout === null && localFrame > entryDuration - OPACITY_EXIT_FRAMES - 1) {
    opacity = interpolate(localFrame, [entryDuration - OPACITY_EXIT_FRAMES, entryDuration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }

  // Full-screen subtle Ken Burns
  const fsScale = layout === "full-screen"
    ? interpolate(localFrame, [0, entryDuration], [1.0, FS_KENBURNS_MAX], { extrapolateRight: "clamp" })
    : 1;
  const fsEnterScale = (layout === "full-screen" && isEnterChange)
    ? interpolate(localFrame, FS_ENTER_SETTLE_FRAMES, [FS_ENTER_SCALE, 0.99, 1.0], { extrapolateRight: "clamp" })
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

  // From full-screen: avatar slides DOWN FULL_TO_SPLIT_SLIDE_PX to reach split-screen top edge
  // Normal enter: slides UP SPLIT_ENTER_SLIDE_FROM_PX from below
  const slideY = isFromFullScreen
    ? interpolate(slideIn, [0, 1], [-FULL_TO_SPLIT_SLIDE_PX, 0])
    : interpolate(slideIn, [0, 1], [SPLIT_ENTER_SLIDE_FROM_PX, 0]);
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
    height: `${SPLIT_HEIGHT_PCT}%`,
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
            height: ACCENT_LINE_HEIGHT_PX,
            background: "linear-gradient(90deg, transparent, rgba(66,133,244,0.6) 50%, transparent)",
            zIndex: 2,
          }} />
          <div style={{
            position: "absolute",
            top: 0, left: 0, right: 0,
            height: ACCENT_GRADIENT_HEIGHT_PX,
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
