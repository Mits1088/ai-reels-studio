import React from "react";
import {
  AbsoluteFill, Audio, Sequence, staticFile, Img,
  useCurrentFrame, interpolate, OffthreadVideo,
} from "remotion";
import type { Timeline, TimelineEntry, OverlayEntry } from "./types";
import { toFrame } from "./utils";

// Components used by the generic renderer
import { OverlayKeyword } from "./components/effects/OverlayKeyword";
import { BadgePopup }      from "./components/effects/BadgePopup";
import { KeywordFadeIn }   from "./components/effects/KeywordFadeIn";
import { NumberPopup }     from "./components/effects/NumberPopup";
import { NoiseOverlay }    from "./components/effects/NoiseOverlay";
import { PunchInZoom }     from "./components/effects/PunchInZoom";
import { Caption }         from "./components/Caption";
import { AvatarVideo }     from "./components/media/AvatarVideo";
import { FramedImage }     from "./components/media/FramedImage";

// ── Overlay component registry ────────────────────────────────────────────
// Maps overlay type strings from timeline.json to React components.
// Covers ~95% of actual usage across all projects.
// Add new types here as they appear in real timelines.
const OVERLAY_REGISTRY: Record<string, React.FC<any>> = {
  OverlayKeyword,
  BadgePopup,
  KeywordFadeIn,
  NumberPopup,
};

// ── Helpers ───────────────────────────────────────────────────────────────

const SPLIT_H = "40%";
const splitTopStyle: React.CSSProperties = {
  position: "absolute", top: 0, left: 0, right: 0,
  height: SPLIT_H, overflow: "hidden", zIndex: 10,
};

/** Compute center-full ranges from demo + broll entries with display: "center-full" */
function computeCenterFullRanges(timeline: Timeline): { start: number; end: number }[] {
  const ranges: { start: number; end: number }[] = [];
  const entries = [
    ...(timeline.lanes.demo || []),
    ...(timeline.lanes.broll || []),
  ];
  for (const e of entries) {
    if (e.display === "center-full") {
      ranges.push({ start: e.start, end: e.end });
    }
  }
  // Merge overlapping/adjacent ranges
  ranges.sort((a, b) => a.start - b.start);
  const merged: { start: number; end: number }[] = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (last && r.start <= last.end + 0.1) {
      last.end = Math.max(last.end, r.end);
    } else {
      merged.push({ ...r });
    }
  }
  return merged;
}

/** Determine background color based on avatar layout at a given time */
function getBackgroundAtTime(avatarEntries: TimelineEntry[], time: number): string {
  for (const e of avatarEntries) {
    if (time >= e.start && time < e.end) {
      return e.layout === "full-screen" ? "#1A1A2E" : "#FFFFFF";
    }
  }
  return "#F5F5F5"; // no avatar = center-full content
}

/** Build background segments from avatar lane transitions */
function buildBackgroundSegments(
  avatarEntries: TimelineEntry[], totalDuration: number
): { start: number; end: number; color: string }[] {
  const segments: { start: number; end: number; color: string }[] = [];
  const step = 0.5; // sample every 0.5s
  let currentColor = getBackgroundAtTime(avatarEntries, 0);
  let segStart = 0;

  for (let t = step; t <= totalDuration; t += step) {
    const color = getBackgroundAtTime(avatarEntries, t);
    if (color !== currentColor) {
      segments.push({ start: segStart, end: t, color: currentColor });
      currentColor = color;
      segStart = t;
    }
  }
  segments.push({ start: segStart, end: totalDuration, color: currentColor });
  return segments;
}

/** Background crossfade helper */
const SeamCrossfade: React.FC<{
  fromSec: number; durFrames: number; children: React.ReactNode;
}> = ({ fromSec, durFrames, children }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - toFrame(fromSec);
  const opacity = interpolate(localFrame, [0, durFrames], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <div style={{ opacity, position: "absolute", inset: 0 }}>{children}</div>;
};

/** Check if an asset is a video by extension */
function isVideo(asset: string): boolean {
  return /\.(mp4|webm|mov)$/i.test(asset);
}

// ── Main Composition ──────────────────────────────────────────────────────

export const GenericReelComposition: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  const centerFullRanges = computeCenterFullRanges(timeline);
  const bgSegments = buildBackgroundSegments(timeline.lanes.avatar, timeline.total_duration);

  return (
    <AbsoluteFill style={{ background: "#000000" }}>

      {/* ════════ BACKGROUNDS ════════ */}
      {bgSegments.map((seg, i) => (
        <Sequence
          key={`bg-${i}`}
          from={toFrame(seg.start)}
          durationInFrames={Math.max(1, toFrame(seg.end - seg.start))}
        >
          {i === 0 ? (
            <AbsoluteFill style={{ background: seg.color }} />
          ) : (
            <SeamCrossfade fromSec={seg.start} durFrames={8}>
              <AbsoluteFill style={{ background: seg.color }} />
            </SeamCrossfade>
          )}
        </Sequence>
      ))}

      {/* ════════ AUDIO ════════ */}
      <Audio src={staticFile(timeline.audio ?? "source.wav")} volume={1} />

      {timeline.lanes.sfx.map((entry, i) => (
        <Sequence
          key={`sfx-${i}`}
          from={toFrame(entry.start)}
          durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
        >
          <Audio src={staticFile(entry.asset!)} volume={entry.volume ?? 0.25} />
        </Sequence>
      ))}

      {(timeline.lanes.music || []).map((entry, i) => (
        <Sequence
          key={`music-${i}`}
          from={toFrame(entry.start)}
          durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
        >
          <Audio src={staticFile(entry.asset!)} volume={entry.volume ?? 0.15} />
        </Sequence>
      ))}

      {/* ════════ BROLL (center-full videos) ════════ */}
      {(timeline.lanes.broll || []).map((entry, i) => {
        if (entry.display !== "center-full" || !entry.asset) return null;
        return (
          <Sequence
            key={`broll-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
            premountFor={10}
          >
            <AbsoluteFill style={{ zIndex: 12, background: "transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
              {isVideo(entry.asset) ? (
                <OffthreadVideo
                  src={staticFile(entry.asset)}
                  muted
                  playbackRate={entry.playbackRate ?? 1}
                  style={{ width: "100%", height: "100%", objectFit: "contain" }}
                />
              ) : (
                <Img
                  src={staticFile(entry.asset)}
                  style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "center" }}
                />
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* ════════ DEMO IMAGES (split-screen with zoom) ════════ */}
      {(timeline.lanes.demo || []).map((entry, i) => {
        if (!entry.asset) return null;
        const isCenterFull = entry.display === "center-full";

        if (isCenterFull) {
          return (
            <Sequence
              key={`demo-cf-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {isVideo(entry.asset) ? (
                  <OffthreadVideo
                    src={staticFile(entry.asset)}
                    muted
                    playbackRate={entry.playbackRate ?? 1}
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                  />
                ) : (
                  <FramedImage
                    src={entry.asset}
                    splitScreen={false}
                    zoomMoments={entry.zoom_moments}
                  />
                )}
              </AbsoluteFill>
            </Sequence>
          );
        }

        // Default: split-screen demo in top 40%
        return (
          <Sequence
            key={`demo-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
            premountFor={5}
          >
            <div style={splitTopStyle}>
              {isVideo(entry.asset) ? (
                <OffthreadVideo
                  src={staticFile(entry.asset)}
                  muted
                  playbackRate={entry.playbackRate ?? 1}
                  style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
                />
              ) : (
                <FramedImage
                  src={entry.asset}
                  splitScreen
                  zoomMoments={entry.zoom_moments}
                />
              )}
            </div>
          </Sequence>
        );
      })}

      {/* ════════ SUPPORT (same as demo, split-screen default) ════════ */}
      {(timeline.lanes.support || []).map((entry, i) => {
        if (!entry.asset) return null;
        return (
          <Sequence
            key={`support-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
          >
            <div style={splitTopStyle}>
              {isVideo(entry.asset) ? (
                <OffthreadVideo
                  src={staticFile(entry.asset)}
                  muted
                  style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
                />
              ) : (
                <FramedImage
                  src={entry.asset}
                  splitScreen
                  zoomMoments={entry.zoom_moments}
                />
              )}
            </div>
          </Sequence>
        );
      })}

      {/* ════════ AVATAR ════════ */}
      <AvatarVideo
        entries={timeline.lanes.avatar}
        hideRanges={centerFullRanges}
      />

      {/* ════════ OVERLAYS (data-driven from overlays lane) ════════ */}
      {(timeline.lanes.overlays || []).map((entry: OverlayEntry, i: number) => {
        const Component = OVERLAY_REGISTRY[entry.type];
        if (!Component) {
          // Log unsupported type for debugging — won't crash render
          if (typeof console !== "undefined") {
            console.warn(`GenericReel: unsupported overlay type "${entry.type}" at ${entry.start}s`);
          }
          return null;
        }
        const dur = Math.max(1, toFrame(entry.end - entry.start));
        const props = entry.props || {};

        // BadgePopup and NumberPopup need a positioning wrapper
        const needsWrapper = entry.type === "BadgePopup" || entry.type === "NumberPopup";

        return (
          <Sequence
            key={`overlay-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={dur}
          >
            {needsWrapper ? (
              <AbsoluteFill style={{
                display: "flex", alignItems: "flex-start", justifyContent: "center",
                paddingTop: 80, zIndex: 20,
              }}>
                <Component durationInFrames={dur} {...props} />
              </AbsoluteFill>
            ) : (
              <Component durationInFrames={dur} {...props} />
            )}
          </Sequence>
        );
      })}

      {/* ════════ CAPTIONS ════════ */}
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

      {/* ════════ NOISE ════════ */}
      <NoiseOverlay opacity={0.03} />

    </AbsoluteFill>
  );
};
