import React from "react";
import {
  AbsoluteFill, Audio, Sequence, staticFile, Img,
  useCurrentFrame, interpolate, OffthreadVideo, spring, useVideoConfig,
} from "remotion";
import type { Timeline, TimelineEntry, OverlayEntry, TransitionPreset, ZoomMoment } from "./types";
import { toFrame, CONTENT_HEIGHT_PCT } from "./utils";

// Components used by the generic renderer
import { OverlayKeyword }    from "./components/effects/OverlayKeyword";
import { BadgePopup }        from "./components/effects/BadgePopup";
import { KeywordFadeIn }     from "./components/effects/KeywordFadeIn";
import { NumberPopup }       from "./components/effects/NumberPopup";
import { NoiseOverlay }      from "./components/effects/NoiseOverlay";
import { PunchInZoom }       from "./components/effects/PunchInZoom";
import { HeroTextCard }      from "./components/effects/HeroTextCard";
import { CardStack }         from "./components/effects/CardStack";
import { FlashReset }        from "./components/effects/FlashReset";
import { StrikethroughSwap } from "./components/effects/StrikethroughSwap";
import { LogoOverlay }       from "./components/effects/LogoOverlay";
import { FeatureMockup }     from "./components/effects/FeatureMockup";
// clippkit (vendored, MIT) — see remotion/src/components/effects/clippkit/NOTICE.md
import { BarWaveform }       from "./components/effects/clippkit/BarWaveform";
import { CircularWaveform }  from "./components/effects/clippkit/CircularWaveform";
import { GlitchText }        from "./components/effects/clippkit/GlitchText";
import { TypingText }        from "./components/effects/clippkit/TypingText";
import { ToastCard }         from "./components/effects/clippkit/ToastCard";
import { Caption }           from "./components/Caption";
import { AvatarVideo }       from "./components/media/AvatarVideo";
import { FramedImage }       from "./components/media/FramedImage";
import { ImageGrid2x2 }      from "./components/media/ImageGrid2x2";
import { ScrollImage }       from "./components/media/ScrollImage";
import { GuidedDemo }        from "./components/effects/GuidedDemo";
import { AnnotationCircle }  from "./components/effects/AnnotationCircle";
import { CharKeyword }       from "./components/effects/CharKeyword";
import { TerminalWindow }    from "./components/effects/TerminalWindow";
import { StatCounter }       from "./components/effects/StatCounter";
import { ComparisonSlider }  from "./components/effects/ComparisonSlider";
import { TextHighlight }     from "./components/effects/TextHighlight";
import { ChartBar }          from "./components/effects/ChartBar";
import { ProgressSteps }     from "./components/effects/ProgressSteps";
import { HighlightBox }      from "./components/effects/HighlightBox";
import { SourceProofCard }   from "./components/effects/SourceProofCard";
import { LowerThird }        from "./components/effects/LowerThird";
import { PunchText }         from "./components/effects/PunchText";
import { KineticQuote }      from "./components/effects/KineticQuote";
import { ProgressRing }      from "./components/effects/ProgressRing";
import { TypingInput }       from "./components/effects/TypingInput";
import { TypewriterCode }    from "./components/effects/TypewriterCode";
import { SceneBreak }        from "./components/effects/SceneBreak";
import { LottieOverlay }     from "./components/effects/LottieOverlay";
import { ChapterDivider }    from "./components/effects/ChapterDivider";
import { ComparisonGrid }    from "./components/effects/ComparisonGrid";
import { ScrollingIconGrid } from "./components/effects/ScrollingIconGrid";
import { CursorClick }       from "./components/effects/CursorClick";
import { LightLeakOverlay }  from "./components/effects/LightLeakOverlay";
import { AppWindow }         from "./components/media/AppWindow";
import { TransitionWrapper } from "./components/transitions/TransitionWrapper";

// ── Overlay component registry ────────────────────────────────────────────
// Maps overlay type strings from timeline.json to React components.
// Covers ~95% of actual usage across all projects.
// Add new types here as they appear in real timelines.
const OVERLAY_REGISTRY: Record<string, React.FC<any>> = {
  OverlayKeyword,
  BadgePopup,
  KeywordFadeIn,
  NumberPopup,
  HeroTextCard,
  CardStack,
  FlashReset,
  StrikethroughSwap,
  LogoOverlay,
  FeatureMockup,
  // clippkit (vendored MIT)
  BarWaveform,
  CircularWaveform,
  GlitchText,
  TypingText,
  ToastCard,
  // annotation
  AnnotationCircle,
  // char-level explosive reveals
  CharKeyword,
  // terminal window with macOS chrome + typing animation
  TerminalWindow,
  // animated number count-up
  StatCounter,
  // before/after comparison slider
  ComparisonSlider,
  // text with highlight sweep
  TextHighlight,
  // data-driven bar chart
  ChartBar,
  // numbered steps with connecting line
  ProgressSteps,
  // rectangular UI highlight box (alternative to AnnotationCircle for rectangular targets)
  HighlightBox,
  // styled social-proof tweet/post card
  SourceProofCard,
  // broadcast-style lower-third name badge
  LowerThird,
  // slam-in with echo ripple (single explosive word)
  PunchText,
  // word-by-word kinetic quote reveal
  KineticQuote,
  // countdown / progress ring (@remotion/shapes)
  ProgressRing,
  // product-accurate input field typing animation
  TypingInput,
  // single-line terminal code typing
  TypewriterCode,
  // GPU-safe whip/iris transition flash
  SceneBreak,
  // animated brand logo from Lottie JSON
  LottieOverlay,
  // tool introduction chapter divider (logo + title full-frame)
  ChapterDivider,
  // side-by-side screenshot comparison with VS divider
  ComparisonGrid,
  // rotated scrolling icon grid (hook background)
  ScrollingIconGrid,
  // cursor click-point ripple animation
  CursorClick,
  // WebGL light flare transition (@remotion/light-leaks)
  LightLeakOverlay,
};

// ── Helpers ───────────────────────────────────────────────────────────────

const SPLIT_H = `${CONTENT_HEIGHT_PCT}%`;
const splitTopStyle: React.CSSProperties = {
  position: "absolute", top: 0, left: 0, right: 0,
  height: SPLIT_H, overflow: "hidden", zIndex: 10,
};

/** Compute center-full ranges from demo + broll entries that hide the avatar */
function computeCenterFullRanges(timeline: Timeline): { start: number; end: number }[] {
  const ranges: { start: number; end: number }[] = [];
  const entries = [
    ...(timeline.lanes.demo || []),
    ...(timeline.lanes.broll || []),
  ];
  for (const e of entries) {
    if (
      e.display === "center-full" ||
      e.display === "guided-demo" ||
      e.display === "image-grid" ||
      e.display === "scroll-image"
    ) {
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

/** Determine background color based on avatar layout at a given time.
 *  Honors per-entry `bgColor` override (used by proof-escalation-editorial
 *  for warm beige #FAF9F5, dark #1A1A1A, etc). Falls back to layout-derived
 *  defaults for cinematic-presenter style. */
function getBackgroundAtTime(avatarEntries: TimelineEntry[], time: number): string {
  for (const e of avatarEntries) {
    if (time >= e.start && time < e.end) {
      if (e.bgColor) return e.bgColor;
      return e.layout === "full-screen" ? "#1A1A2E" : "#FFFFFF";
    }
  }
  return "#F8F8F8"; // no avatar = gallery/center-full content
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

/** Background crossfade helper.
 *  Note: this component is rendered inside a parent <Sequence>, so
 *  useCurrentFrame() already returns the local frame (starting from 0
 *  at the Sequence start). Do NOT subtract `fromSec` — that would push
 *  localFrame negative and clamp opacity to 0, making every bg segment
 *  after the first invisible. The fromSec prop is now unused but kept
 *  in the signature for backwards compatibility with any callers. */
const SeamCrossfade: React.FC<{
  fromSec: number; durFrames: number; children: React.ReactNode;
}> = ({ durFrames, children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, durFrames], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <div style={{ opacity, position: "absolute", inset: 0 }}>{children}</div>;
};

/** Check if an asset is a video by extension */
function isVideo(asset: string): boolean {
  return /\.(mp4|webm|mov)$/i.test(asset);
}

// ── Helpers ───────────────────────────────────────────────────────────────

/** @sfx/ shorthand → @remotion/sfx CDN URLs */
const SFX_MAP: Record<string, string> = {
  "@sfx/whoosh":        "https://remotion.media/whoosh.wav",
  "@sfx/whip":          "https://remotion.media/whip.wav",
  "@sfx/pageTurn":      "https://remotion.media/page-turn.wav",
  "@sfx/uiSwitch":      "https://remotion.media/switch.wav",
  "@sfx/mouseClick":    "https://remotion.media/mouse-click.wav",
  "@sfx/shutterModern": "https://remotion.media/shutter-modern.wav",
  "@sfx/shutterOld":    "https://remotion.media/shutter-old.wav",
  "@sfx/ding":          "https://remotion.media/ding.wav",
  "@sfx/bruh":          "https://remotion.media/bruh.wav",
  "@sfx/vineBoom":      "https://remotion.media/vine-boom.wav",
};

/** Resolve @sfx/ shorthand, https:// CDN URLs, or local staticFile paths */
const resolveAudioSrc = (asset: string): string => {
  if (SFX_MAP[asset]) return SFX_MAP[asset];
  if (asset.startsWith("https://")) return asset;
  return staticFile(asset);
};

// ── Gallery helper components (defined outside main component for hook validity) ──

/** Center-full image with slow ambient scale push toward a focal point */
const AmbientZoomImage: React.FC<{
  src: string;
  durationInFrames: number;
  fromScale: number;
  toScale: number;
  targetX: number;
  targetY: number;
}> = ({ src, durationInFrames, fromScale, toScale, targetX, targetY }) => {
  const frame = useCurrentFrame();
  const scaleFactor = interpolate(
    frame,
    [0, Math.max(1, durationInFrames)],
    [fromScale, toScale],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: "center",
          transform: `scale(${scaleFactor})`,
          transformOrigin: `${targetX}% ${targetY}%`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Center-full image with spring-based punch-in zoom at specified moments */
const ZoomedCenterFullImage: React.FC<{
  src: string;
  zoomMoments: ZoomMoment[];
}> = ({ src, zoomMoments }) => (
  <AbsoluteFill>
    <PunchInZoom moments={zoomMoments}>
      <Img
        src={staticFile(src)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: "center",
          display: "block",
        }}
      />
    </PunchInZoom>
  </AbsoluteFill>
);

/** Spring scale-settle + fade-in entry wrapper for center-full demo/broll sections */
const CenterFullEntry: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sv = spring({ frame, fps, config: { damping: 18, stiffness: 160, mass: 0.9 } });
  const entryScale = interpolate(sv, [0, 1], [1.05, 1.0]);
  const fadeIn = interpolate(frame, [0, 5], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{
      width: "100%", height: "100%",
      transform: `scale(${entryScale})`,
      opacity: fadeIn,
      overflow: "hidden",
    }}>
      {children}
    </div>
  );
};

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
            <AbsoluteFill style={{ background: seg.color, zIndex: 0 }} />
          ) : (
            <SeamCrossfade fromSec={seg.start} durFrames={8}>
              <AbsoluteFill style={{ background: seg.color, zIndex: 0 }} />
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
          <Audio src={resolveAudioSrc(entry.asset!)} volume={entry.volume ?? 0.25} />
        </Sequence>
      ))}

      {(timeline.lanes.music || []).map((entry, i) => (
        <Sequence
          key={`music-${i}`}
          from={toFrame(entry.start)}
          durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
        >
          <Audio src={resolveAudioSrc(entry.asset!)} volume={entry.volume ?? 0.15} />
        </Sequence>
      ))}

      {/* ════════ BROLL (gallery: center-full, image-grid, scroll-image) ════════ */}
      {(timeline.lanes.broll || []).map((entry, i) => {
        const dur = Math.max(1, toFrame(entry.end - entry.start));

        // ── Image grid (ImageGrid2x2) ─────────────────────────────────────
        if (entry.display === "image-grid" && entry.images) {
          return (
            <Sequence
              key={`broll-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12 }}>
                <ImageGrid2x2
                  images={entry.images}
                  durationInFrames={dur}
                  staggerDelays={entry.staggerDelays}
                  dissolveFromPrevious={entry.dissolveFromPrevious}
                  bookSpreadIndex={entry.bookSpreadIndex}
                />
              </AbsoluteFill>
            </Sequence>
          );
        }

        // ── Scroll image (vertical reveal for tall portraits) ─────────────
        if (entry.display === "scroll-image" && entry.asset && entry.imageAspectRatio) {
          return (
            <Sequence
              key={`broll-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12 }}>
                <ScrollImage
                  src={entry.asset}
                  durationInFrames={dur}
                  imageAspectRatio={entry.imageAspectRatio}
                />
              </AbsoluteFill>
            </Sequence>
          );
        }

        // ── Center-full: video or image (with optional ambient/zoom) ──────
        if (entry.display === "center-full" && entry.asset) {
          let inner: React.ReactNode;

          if (isVideo(entry.asset)) {
            inner = (
              <OffthreadVideo
                src={staticFile(entry.asset)}
                muted
                playbackRate={entry.playbackRate ?? 1}
                style={{
                  width: "100%", height: "100%",
                  objectFit: "contain",
                  transform: "scale(1.5)",
                  transformOrigin: "center center",
                }}
              />
            );
          } else if (entry.ambient_zoom) {
            inner = (
              <AmbientZoomImage
                src={entry.asset}
                durationInFrames={dur}
                fromScale={entry.ambient_zoom.fromScale}
                toScale={entry.ambient_zoom.toScale}
                targetX={entry.ambient_zoom.targetX}
                targetY={entry.ambient_zoom.targetY}
              />
            );
          } else if (entry.zoom_moments && entry.zoom_moments.length > 0) {
            inner = (
              <ZoomedCenterFullImage
                src={entry.asset}
                zoomMoments={entry.zoom_moments}
              />
            );
          } else {
            inner = (
              <Img
                src={staticFile(entry.asset)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: "center",
                  display: "block",
                }}
              />
            );
          }

          return (
            <Sequence
              key={`broll-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12, background: "transparent" }}>
                {inner}
              </AbsoluteFill>
            </Sequence>
          );
        }

        return null;
      })}

      {/* ════════ DEMO IMAGES ════════ */}
      {(timeline.lanes.demo || []).map((entry, i) => {
        if (!entry.asset) return null;
        const dur = Math.max(1, toFrame(entry.end - entry.start));

        // ── Guided demo: browser frame + virtual camera pan + spotlight ──
        if (entry.display === "guided-demo") {
          return (
            <Sequence
              key={`demo-gd-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12 }}>
                {isVideo(entry.asset) ? (
                  <OffthreadVideo
                    src={staticFile(entry.asset)}
                    muted
                    playbackRate={entry.playbackRate ?? 1}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                ) : (
                  <GuidedDemo
                    asset={entry.asset}
                    durationInFrames={dur}
                    guidedDemo={entry.guided_demo}
                  />
                )}
              </AbsoluteFill>
            </Sequence>
          );
        }

        // ── Center-full: full-frame video or image ───────────────────────
        if (entry.display === "center-full") {
          return (
            <Sequence
              key={`demo-cf-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={10}
            >
              <AbsoluteFill style={{ zIndex: 12 }}>
                <CenterFullEntry durationInFrames={dur}>
                  {isVideo(entry.asset) ? (
                    <OffthreadVideo
                      src={staticFile(entry.asset)}
                      muted
                      playbackRate={entry.playbackRate ?? 1}
                      style={{
                        width: "100%", height: "100%",
                        objectFit: "contain",
                        transform: "scale(1.5)",
                        transformOrigin: "center center",
                      }}
                    />
                  ) : (
                    <Img
                      src={staticFile(entry.asset)}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                        display: "block",
                      }}
                    />
                  )}
                </CenterFullEntry>
              </AbsoluteFill>
            </Sequence>
          );
        }

        // ── App-window: asset wrapped in browser/app chrome ────────────
        if (entry.display === "app-window" && entry.asset) {
          const windowContent = isVideo(entry.asset) ? (
            <OffthreadVideo
              src={staticFile(entry.asset)}
              muted
              playbackRate={entry.playbackRate ?? 1}
              style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
            />
          ) : (
            <FramedImage src={entry.asset} zoomMoments={entry.zoom_moments} />
          );
          return (
            <Sequence
              key={`demo-aw-${i}`}
              from={toFrame(entry.start)}
              durationInFrames={dur}
              premountFor={5}
            >
              <div style={splitTopStyle}>
                <div style={{ width: "100%", height: "100%", padding: "14px 18px" }}>
                  <AppWindow
                    platform={entry.appWindow?.platform}
                    theme={entry.appWindow?.theme}
                    url={entry.appWindow?.url}
                    title={entry.appWindow?.title}
                    showUrlBar={entry.appWindow?.showUrlBar}
                  >
                    {windowContent}
                  </AppWindow>
                </div>
              </div>
            </Sequence>
          );
        }

        // ── Default: split-screen demo in top 40% ───────────────────────
        const splitContent = isVideo(entry.asset) ? (
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
        );
        return (
          <Sequence
            key={`demo-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={dur}
            premountFor={5}
          >
            <div style={splitTopStyle}>
              {entry.transition_preset ? (
                <TransitionWrapper
                  durationInFrames={dur}
                  preset={entry.transition_preset as TransitionPreset}
                >
                  {splitContent}
                </TransitionWrapper>
              ) : splitContent}
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

        // BadgePopup, NumberPopup, and CardStack need a top-anchored
        // positioning wrapper. Other overlays (HeroTextCard, OverlayKeyword,
        // FlashReset, StrikethroughSwap) self-position via their own
        // AbsoluteFill — but they STILL need an explicit zIndex 20 wrapper
        // so they render ABOVE the avatar (zIndex 5/10), not behind it.
        const needsTopAnchoredWrapper =
          entry.type === "BadgePopup" ||
          entry.type === "NumberPopup" ||
          entry.type === "CardStack";

        return (
          <Sequence
            key={`overlay-${i}`}
            from={toFrame(entry.start)}
            durationInFrames={dur}
          >
            {needsTopAnchoredWrapper ? (
              <AbsoluteFill style={{
                display: "flex", alignItems: "flex-start", justifyContent: "center",
                paddingTop: 80, zIndex: 20,
              }}>
                <Component durationInFrames={dur} {...props} />
              </AbsoluteFill>
            ) : (
              <AbsoluteFill style={{ zIndex: 20 }}>
                <Component durationInFrames={dur} {...props} />
              </AbsoluteFill>
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
