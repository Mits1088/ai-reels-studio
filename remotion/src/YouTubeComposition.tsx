import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  OffthreadVideo,
} from "remotion";
import type { YouTubeTimeline, OverlayEntry } from "./types";
import { toFrame } from "./utils";

// ── Existing components (reusable from reel pipeline) ──────────────
import { BadgePopup } from "./components/effects/BadgePopup";
import { KeywordFadeIn } from "./components/effects/KeywordFadeIn";
import { NumberPopup } from "./components/effects/NumberPopup";
import { OverlayKeyword } from "./components/effects/OverlayKeyword";
import { AnnotationCircle } from "./components/effects/AnnotationCircle";
import { CursorClick } from "./components/effects/CursorClick";
import { ChapterDivider } from "./components/effects/ChapterDivider";
import { FlashReset } from "./components/effects/FlashReset";
import { HeroTextCard } from "./components/effects/HeroTextCard";
import { LowerThird } from "./components/effects/LowerThird";
import { NoiseOverlay } from "./components/effects/NoiseOverlay";
import { Caption } from "./components/Caption";

// ── New YouTube-specific components ────────────────────────────────
import { HighlightBox } from "./components/effects/HighlightBox";
import { LinkOverlay } from "./components/effects/LinkOverlay";
import { EndScreen } from "./components/effects/EndScreen";
import { SubscribeCTA } from "./components/effects/SubscribeCTA";

// ── Component registry ─────────────────────────────────────────────
// Maps overlay type strings from youtube-timeline.json to React components.
// To add a new overlay type: import it above, add it here.
const OVERLAY_REGISTRY: Record<string, React.FC<any>> = {
  // Reusable from reel pipeline
  BadgePopup,
  KeywordFadeIn,
  NumberPopup,
  OverlayKeyword,
  AnnotationCircle,
  CursorClick,
  ChapterDivider,
  FlashReset,
  HeroTextCard,
  LowerThird,

  // YouTube-specific
  HighlightBox,
  LinkOverlay,
  EndScreen,
  SubscribeCTA,
};

// ── Composition ────────────────────────────────────────────────────

export const YouTubeComposition: React.FC<{
  timeline: YouTubeTimeline;
}> = ({ timeline }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {/* Layer 0 — Base YouTube video (full frame) */}
      <AbsoluteFill style={{ zIndex: 0 }}>
        <OffthreadVideo
          src={staticFile(timeline.video)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
          muted={false}
        />
      </AbsoluteFill>

      {/* Layer 1 — SFX audio */}
      {timeline.lanes.sfx?.map((entry, i) => {
        const dur = Math.max(1, toFrame(entry.end - entry.start));
        return (
          <Sequence
            key={`sfx-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={dur}
          >
            <Audio
              src={staticFile(entry.asset!)}
              volume={entry.volume ?? 0.2}
            />
          </Sequence>
        );
      })}

      {/* Layer 2 — Music */}
      {timeline.lanes.music?.map((entry, i) => {
        const dur = Math.max(1, toFrame(entry.end - entry.start));
        return (
          <Sequence
            key={`music-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={dur}
          >
            <Audio
              src={staticFile(entry.asset!)}
              volume={entry.volume ?? 0.1}
            />
          </Sequence>
        );
      })}

      {/* Layer 3 — Overlays (the main enhancement layer) */}
      <AbsoluteFill style={{ zIndex: 10 }}>
        {timeline.lanes.overlays.map((entry, i) => {
          const Component = OVERLAY_REGISTRY[entry.type];
          if (!Component) {
            console.warn(
              `YouTubeComposition: unknown overlay type "${entry.type}" at ${entry.start}s`
            );
            return null;
          }
          const dur = Math.max(1, toFrame(entry.end - entry.start));
          return (
            <Sequence
              key={`overlay-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={15}
            >
              <Component
                {...(entry.props ?? {})}
                durationInFrames={dur}
              />
            </Sequence>
          );
        })}
      </AbsoluteFill>

      {/* Layer 4 — Captions (optional — YouTube has its own, but styled captions add polish) */}
      {timeline.lanes.captions && (
        <AbsoluteFill style={{ zIndex: 20 }}>
          {timeline.lanes.captions.map((cap, i) => {
            const dur = Math.max(1, toFrame(cap.end - cap.start));
            return (
              <Sequence
                key={`cap-${i}`}
                from={toFrame(cap.start)}
                durationInFrames={dur}
              >
                <Caption text={cap.text!} durationInFrames={dur} />
              </Sequence>
            );
          })}
        </AbsoluteFill>
      )}

      {/* Layer 5 — Film grain (subtle texture) */}
      <AbsoluteFill style={{ zIndex: 30, pointerEvents: "none" }}>
        <NoiseOverlay />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
