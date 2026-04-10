import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

/**
 * HookIntroScene — beat-01 hook intro (0.0–3.18s / 95 frames at 30fps)
 *
 * Motion budget: 1 hero, 1 support, 1 accent.
 *
 *   Hero:    panel wipe — spring-driven clipPath reveal from top (frames 4–20)
 *   Support: avatar scale settle — 1.03 → 1.00 (frames 0–6)
 *   Accent:  divider line fade (frames 10–20)
 *
 * Hold (frames 20–93): slow Ken Burns on top panel (1.5% scale drift toward
 * the Claude logo). Not dead, not distracting.
 *
 * Layout:
 *   Top 38%  — panel video (Hook.mp4 from 4s): Claude homepage/logo loading
 *   Bottom 62% — avatar: visible from frame 0, human anchor first
 *
 * Integration:
 *   <Sequence from={0} durationInFrames={95}>
 *     <HookIntroScene avatarSrc="..." panelSrc="..." durationInFrames={95} />
 *   </Sequence>
 *   Add { start: 0, end: 3.18 } to AvatarVideo hideRanges.
 */

const PANEL_HEIGHT_PCT = 38;
const AVATAR_HEIGHT_PCT = 62;
const HOOK_PANEL_START_SEC = 5.0;

export const HookIntroScene: React.FC<{
  avatarSrc: string;
  panelSrc: string;
  durationInFrames: number;
}> = ({ avatarSrc, panelSrc, durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── SUPPORT: avatar scale settle 1.03 → 1.00, frames 0–6 ──────────────
  const avatarScale = interpolate(frame, [0, 6], [1.03, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── HERO: panel wipe — spring clipPath reveal from top, frames 4–20 ────
  const wipeSpring = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 200, stiffness: 160, mass: 0.4 },
    durationInFrames: 16,
  });
  const clipInset = interpolate(wipeSpring, [0, 1], [100, 0], {
    extrapolateRight: "clamp",
  });

  // ── ACCENT: divider fade, frames 10–20 ─────────────────────────────────
  const dividerOpacity = interpolate(frame, [10, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── HOLD: slow Ken Burns on top panel, frames 20–93 ────────────────────
  // 1.5% scale drift toward center — barely perceptible, keeps panel alive
  const holdScale = interpolate(frame, [20, durationInFrames], [1.0, 1.015], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>

      {/* ════ TOP PANEL: wipe reveal from top ════ */}
      <div
        style={{
          position: "absolute",
          top: 0, left: 0, right: 0,
          height: `${PANEL_HEIGHT_PCT}%`,
          overflow: "hidden",
          zIndex: 11,
          clipPath: `inset(0 0 ${clipInset}% 0)`,
        }}
      >
        <OffthreadVideo
          src={staticFile(panelSrc)}
          muted
          startFrom={Math.round(HOOK_PANEL_START_SEC * fps)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center 45%",
            transform: `scale(${Math.max(holdScale, 1.12)})`,
          }}
        />
      </div>

      {/* ════ AVATAR: bottom 62%, visible from frame 0 ════ */}
      <div
        style={{
          position: "absolute",
          bottom: 0, left: 0, right: 0,
          height: `${AVATAR_HEIGHT_PCT}%`,
          overflow: "hidden",
          zIndex: 10,
          transform: `scale(${avatarScale})`,
          transformOrigin: "bottom center",
        }}
      >
        <OffthreadVideo
          src={staticFile(avatarSrc)}
          muted
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center center",
          }}
        />
      </div>

      {/* ════ DIVIDER: brand line at 38/62 boundary ════ */}
      <div
        style={{
          position: "absolute",
          top: `${PANEL_HEIGHT_PCT}%`,
          left: 0, right: 0,
          height: 2,
          background:
            "linear-gradient(90deg, transparent, rgba(204,120,92,0.75) 25%, rgba(232,184,138,0.95) 50%, rgba(204,120,92,0.75) 75%, transparent)",
          zIndex: 20,
          opacity: dividerOpacity,
        }}
      />

    </AbsoluteFill>
  );
};
