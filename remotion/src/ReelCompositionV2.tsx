import React from "react";
import {
  AbsoluteFill, Audio, Sequence, staticFile,
  useCurrentFrame, interpolate,
} from "remotion";
import type { Timeline, OverlayEntry } from "./types";
import { toFrame } from "./utils";

// ── Backgrounds ──
import { AuroraBackground }  from "./components/effects/AuroraBackground";
import { BackgroundBeams }   from "./components/effects/BackgroundBeams";
import { GradientMesh }      from "./components/effects/GradientMesh";
import { SmokeWisp }         from "./components/effects/SmokeWisp";
import { FocusVignette }     from "./components/effects/FocusVignette";
import { NoiseOverlay }      from "./components/effects/NoiseOverlay";

// ── Effects / Overlays ──
import { KeywordFadeIn } from "./components/effects/KeywordFadeIn";
import { BadgePopup }    from "./components/effects/BadgePopup";
import { NumberPopup }   from "./components/effects/NumberPopup";

// ── NEW: Animated Mock UI Components ──
import { TypingInput }       from "./components/effects/TypingInput";
import { StrikethroughSwap } from "./components/effects/StrikethroughSwap";

// ── Custom Scenes ──
import { HookIntroScene } from "./components/scenes/HookIntroScene";

// ── Content ──
import { Caption }      from "./components/Caption";
import { BRollVideo }   from "./components/media/BRollVideo";
import { AvatarVideo }  from "./components/media/AvatarVideo";

// ════════════════════════════════════════════════════════════════════
// REEL COMPOSITION V2 — Claude 4 Setup Tips (Animated Mock UI version)
//
// Differences from V1:
//   beat-05: TypingInput (Claude style) replaces static screenshot
//   beat-07: TypingInput (Claude style) replaces static screenshot
//   beat-09: StrikethroughSwap replaces broll-result.mp4
//
// Everything else identical to V1:
//   beat-01: HookIntroScene (Hook.mp4 + avatar)
//   beat-02: demo-claude-memory.mp4 center-full (1.83x)
//   beat-04: demo-chatgpt-export.mp4 center-full (2.06x)
//   beat-06: broll-transfer.mp4 center-full
//   beat-08: broll-skills.mp4 center-full
//   beat-10: Avatar full-screen dark CTA
// ════════════════════════════════════════════════════════════════════

const TOTAL = 52.31;

// Background seam: light → dark crossfade before CTA
const SEAM_DARK_START = 43.70;
const SEAM_DARK_END   = 44.36;

// Beams ranges — center-full beats only
const BEAMS_RANGES = [
  { start: 3.50, end: 11.50 },   // beat-02 (tip 1 demo)
  { start: 12.24, end: 18.52 },  // beat-04 (tip 2 demo)
  { start: 23.60, end: 28.28 },  // beat-06 (tip 3 payoff broll)
  { start: 34.96, end: 38.56 },  // beat-08 (tip 4 payoff broll)
] as const;

// ── Icon map for badge overlays ──
const ICON_MAP: Record<string, string> = {
  comment: "💬",
  check:   "✓",
  tip:     "💡",
};

function overlayPositionStyle(position: string): React.CSSProperties {
  const base: React.CSSProperties = {
    position: "absolute",
    zIndex: 50,
    display: "flex",
  };
  switch (position) {
    case "top-right":  return { ...base, top: 80, right: 40 };
    case "top-left":   return { ...base, top: 80, left: 40 };
    case "top-center": return { ...base, top: 80, left: 0, right: 0, justifyContent: "center" };
    default:           return { ...base, top: 80, left: 0, right: 0, justifyContent: "center" };
  }
}

function renderOverlay(overlay: OverlayEntry, i: number) {
  const dur   = toFrame(overlay.end - overlay.start);
  const props = overlay.props ?? {};

  if (overlay.type === "NumberPopup") {
    return (
      <Sequence key={`overlay-${i}`} from={toFrame(overlay.start)} durationInFrames={dur}>
        <NumberPopup
          number={props.number as number}
          label={props.label as string | undefined}
          durationInFrames={dur}
          color={props.color as string | undefined}
          position={props.position as "top-left" | "top-right" | "top-center" | undefined}
        />
      </Sequence>
    );
  }

  if (overlay.type === "BadgePopup") {
    const iconKey  = props.icon as string | undefined;
    const iconChar = iconKey ? (ICON_MAP[iconKey] ?? iconKey) : undefined;
    return (
      <Sequence key={`overlay-${i}`} from={toFrame(overlay.start)} durationInFrames={dur}>
        <div style={overlayPositionStyle((props.position as string) ?? "top")}>
          <BadgePopup
            text={props.label as string ?? ""}
            color={props.color as string | undefined}
            icon={iconChar}
            durationInFrames={dur}
          />
        </div>
      </Sequence>
    );
  }

  return null;
}

// ════════════════════════════════════════════════════════════════════
// Main composition
// ════════════════════════════════════════════════════════════════════

export const ReelCompositionV2: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  const frame = useCurrentFrame();

  const brollEntries   = timeline.lanes.broll ?? [];
  const demoEntries    = timeline.lanes.demo ?? [];
  const overlayEntries = timeline.lanes.overlays ?? [];

  // V2: Only video demos hide avatar (not beat-05/07 since TypingInput uses split-screen with avatar)
  const centerFullRanges = [
    { start: 0, end: 3.24 },  // beat-01: HookIntroScene
    ...demoEntries.filter((e) => e.display === "center-full")
      .map((e) => ({ start: e.start, end: e.end })),
    ...brollEntries.filter((e) => e.display === "center-full")
      .map((e) => ({ start: e.start, end: e.end })),
  ];

  // Background crossfade: light → dark
  const seamDarkProgress = interpolate(
    frame,
    [toFrame(SEAM_DARK_START), toFrame(SEAM_DARK_END)],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ background: "#FFFFFF" }}>

      {/* ════ BACKGROUND: Aurora light (0 → 44.36s) ════ */}
      <Sequence from={0} durationInFrames={toFrame(SEAM_DARK_END)}>
        <AbsoluteFill style={{
          opacity: frame > toFrame(SEAM_DARK_START) ? 1 - seamDarkProgress : 1,
        }}>
          <AuroraBackground
            speed={0.35}
            intensity={0.75}
            colors={[
              "rgba(204, 120,  92, 0.08)",
              "rgba(232, 184, 138, 0.06)",
              "rgba(245, 230, 216, 0.09)",
              "rgba(250, 249, 247, 0.10)",
              "rgba(255, 255, 255, 0.06)",
            ]}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ════ BACKGROUND: Beams — center-full beats ════ */}
      {BEAMS_RANGES.map((r, i) => (
        <Sequence
          key={`beams-${i}`}
          from={toFrame(r.start)}
          durationInFrames={toFrame(r.end - r.start)}
        >
          <BackgroundBeams
            beamCount={6}
            color="rgba(204,120,92,0.04)"
            speed={0.4}
            intensity={0.5}
          />
        </Sequence>
      ))}

      {/* ════ BACKGROUND: Dark outro (43.70 → 52.31s) ════ */}
      <Sequence
        from={toFrame(SEAM_DARK_START)}
        durationInFrames={toFrame(TOTAL - SEAM_DARK_START)}
      >
        <AbsoluteFill style={{
          opacity: frame < toFrame(SEAM_DARK_END) ? seamDarkProgress : 1,
        }}>
          <GradientMesh
            colors={[
              "rgba(204, 120,  92, 0.20)",
              "rgba( 61,  37,  22, 0.75)",
              "rgba( 45,  27,  20, 0.60)",
              "rgba(232, 184, 138, 0.07)",
            ]}
            speed={0.6}
            intensity={1}
          />
          <SmokeWisp count={4} color="rgba(255,255,255,0.025)" speed={0.8} />
          <FocusVignette intensity={0.55} pulseAmount={0.10} />
        </AbsoluteFill>
      </Sequence>

      {/* ════ AUDIO: Narration ════ */}
      <Audio src={staticFile(timeline.audio ?? "source.wav")} volume={1} />

      {/* ════ AUDIO: SFX ════ */}
      {timeline.lanes.sfx.map((entry, i) => (
        <Sequence
          key={`sfx-${i}`}
          from={toFrame(entry.start)}
          durationInFrames={Math.max(1, toFrame(entry.end - entry.start))}
        >
          <Audio src={staticFile(entry.asset!)} volume={entry.volume ?? 0.25} />
        </Sequence>
      ))}

      {/* ════ LAYER: Beat-01 — HookIntroScene ════ */}
      <Sequence from={0} durationInFrames={toFrame(3.24)}>
        <HookIntroScene
          avatarSrc="avatar.mp4"
          panelSrc="hook.mp4"
          durationInFrames={toFrame(3.24)}
        />
      </Sequence>

      {/* ════ LAYER: Demo videos (center-full only — no screenshots in V2) ════ */}
      {demoEntries
        .filter((e) => e.display === "center-full")
        .map((entry, i) => {
          const dur = Math.max(1, toFrame(entry.end - entry.start));
          return (
            <Sequence key={`demo-${i}`} from={toFrame(entry.start)} durationInFrames={dur}>
              <BRollVideo src={entry.asset!} durationInFrames={dur} entry={entry} />
            </Sequence>
          );
        })}

      {/* ════ LAYER: B-Roll videos (center-full) ════ */}
      {brollEntries
        .filter((e) => e.display === "center-full")
        .map((entry, i) => {
          const dur = Math.max(1, toFrame(entry.end - entry.start));
          return (
            <Sequence key={`broll-${i}`} from={toFrame(entry.start)} durationInFrames={dur}>
              <BRollVideo src={entry.asset!} durationInFrames={dur} entry={entry} />
            </Sequence>
          );
        })}

      {/* ════ V2: Beat-05 — TypingInput (Claude style) replaces screenshot ════ */}
      {/* "take that file, drop it into a Claude chat with this prompt" */}
      <Sequence from={toFrame(19.22)} durationInFrames={toFrame(23.60 - 19.22)}>
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          height: "40%",
          overflow: "hidden",
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 24px",
        }}>
          <div style={{ width: "100%" }}>
            <div style={{
              fontSize: 16,
              color: "#888",
              fontFamily: "system-ui, sans-serif",
              textAlign: "center",
              marginBottom: 16,
              fontWeight: 500,
            }}>
              Claude.ai
            </div>
            <TypingInput
              text="Analyze my ChatGPT history. Learn my working style and create a profile of who I am."
              durationInFrames={toFrame(23.60 - 19.22)}
              style="claude"
              typingSpeed={2}
              placeholder="Message Claude..."
              fontSize={20}
            />
          </div>
        </div>
      </Sequence>

      {/* ════ V2: Beat-07 — TypingInput (Claude style) replaces screenshot ════ */}
      {/* "ask it what skills would enhance the work you're currently doing" */}
      <Sequence from={toFrame(28.28)} durationInFrames={toFrame(34.96 - 28.28)}>
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          height: "40%",
          overflow: "hidden",
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 24px",
        }}>
          <div style={{ width: "100%" }}>
            <div style={{
              fontSize: 16,
              color: "#888",
              fontFamily: "system-ui, sans-serif",
              textAlign: "center",
              marginBottom: 16,
              fontWeight: 500,
            }}>
              Claude.ai
            </div>
            <TypingInput
              text="What specific skills would enhance the work I'm currently doing?"
              durationInFrames={toFrame(34.96 - 28.28)}
              style="claude"
              typingSpeed={2}
              placeholder="Message Claude..."
              fontSize={20}
            />
          </div>
        </div>
      </Sequence>

      {/* ════ V2: Beat-09 — StrikethroughSwap replaces broll-result ════ */}
      {/* "That last step alone puts you ahead of 90% of people" */}
      <Sequence from={toFrame(38.98)} durationInFrames={toFrame(44.04 - 38.98)}>
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          height: "40%",
          overflow: "hidden",
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}>
          <StrikethroughSwap
            oldValue="Generic AI assistant"
            newValue="Claude that knows you"
            durationInFrames={toFrame(44.04 - 38.98)}
            strikethroughDelay={12}
            newValueDelay={35}
            fontSize={24}
          />
        </div>
      </Sequence>

      {/* ════ LAYER: Avatar (persistent) ════ */}
      <AvatarVideo entries={timeline.lanes.avatar} hideRanges={centerFullRanges} />

      {/* ════ LAYER: Overlays ════ */}
      {overlayEntries.map((overlay, i) => renderOverlay(overlay, i))}

      {/* ════ LAYER: Captions ════ */}
      {timeline.lanes.captions.map((entry, i) => {
        const dur = Math.max(1, toFrame(entry.end! - entry.start));
        return (
          <Sequence key={`caption-${i}`} from={toFrame(entry.start)} durationInFrames={dur}>
            <Caption text={entry.text!} durationInFrames={dur} />
          </Sequence>
        );
      })}

      {/* ════ LAYER: Film grain ════ */}
      <NoiseOverlay opacity={0.022} />

    </AbsoluteFill>
  );
};
