import React from "react";
import {
  AbsoluteFill, Audio, Sequence, staticFile, Img,
  useCurrentFrame, useVideoConfig, interpolate, OffthreadVideo,
} from "remotion";
import type { Timeline } from "./types";
import { toFrame } from "./utils";

// ── Effects / Overlays ──
import { OverlayKeyword }     from "./components/effects/OverlayKeyword";
import { BadgePopup }         from "./components/effects/BadgePopup";
import { NoiseOverlay }       from "./components/effects/NoiseOverlay";
import { PunchInZoom }        from "./components/effects/PunchInZoom";
// ── Content ──
import { Caption }     from "./components/Caption";
import { AvatarVideo } from "./components/media/AvatarVideo";
import { BRollVideo }  from "./components/media/BRollVideo";
import { FramedImage } from "./components/media/FramedImage";

// ════════════════════════════════════════════════════════════════════
// REEL COMPOSITION — Gemma 4: Open AI That Runs on Your Phone
// STYLE: editorial-authority
//
// Avatar: avatar.mp4 (HeyGen cropped to 1080x1920, 51.15s, 30fps)
// Audio: source.wav (50.88s / 1526 frames)
//
// BEATS (16 sub-beats):
// 01a. HOOK-BRAND   0.00– 2.70  Center-full — Google logo animation
// 01b. HOOK-PROOF   3.16– 5.64  Center-full — ELO chart (20x proof)
// 02.  NAME-REVEAL  6.22– 8.82  Center-full — B-roll model family grid
// 03.  PROOF        9.44–11.98  Center-full — B-roll massive GPU (irony)
// 04a. PROOF       12.62–14.62  Center-full — B-roll device ecosystem
// 04b. PROOF       14.84–15.62  Split — phone demo screenshot
// 04c. TRUST       16.22–17.94  Full-screen — "NEVER LEAVES" on face
// 05.  CONTRADICT  18.52–22.14  Center-full — B-roll Dense 31B + strikethrough
// 06a. PROOF       22.58–26.32  Split — benchmark zoom t2-bench (13x)
// 06b. PROOF       26.84–29.44  Split — benchmark zoom AIME+code
// 07a. PROOF       30.00–33.12  Split — HuggingFace (Apache license)
// 07b. PROOF       33.72–36.98  Split — Ollama (download command)
// 08.  TRUST       37.66–39.58  Full-screen — "400M+" on face
// 09.  RECAP       40.30–42.86  Full-screen — "RUN AND OWN" on face
// 10a. CTA         43.64–48.20  Split — Ollama download path
// 10b. CTA-CLOSE   48.20–50.88  Full-screen — "FOLLOW" on dark
//
// Theme: Gemini/Google AI (blue #4285F4, purple #8E24AA)
// Flash budget: 2/3 (beat-01b hook payoff, beat-08 stat landing)
// ════════════════════════════════════════════════════════════════════

const TOTAL = 50.88;

// Center-full ranges — avatar hides during these
// Must match extended Sequence durations (not beat boundaries)
const centerFullRanges = [
  { start: 6.22,  end: 14.84 },  // beat-02 through beat-04a: all center-full b-roll + title
  { start: 18.52, end: 22.58 },  // beat-05: Dense Architecture b-roll (extended)
];

// Background seam crossfade helper
const SeamCrossfade: React.FC<{
  from: number; dur: number; children: React.ReactNode;
}> = ({ from, dur, children }) => {
  const frame = useCurrentFrame();
  const localFrame = frame - toFrame(from);
  const opacity = interpolate(localFrame, [0, dur], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <div style={{ opacity, position: "absolute", inset: 0 }}>{children}</div>;
};

// Split-screen top zone: 40% to match AvatarVideo split-screen (bottom: 0, height: 60%)
const SPLIT_H = "40%";

const splitTopStyle: React.CSSProperties = {
  position: "absolute", top: 0, left: 0, right: 0,
  height: SPLIT_H, overflow: "hidden", zIndex: 10,
};

// Benchmark table: scrolls horizontally with highlight pause on Gemma 4 column
const BENCH_PAD = 12;
const BENCH_CONTAINER_W = 1080 - BENCH_PAD * 2;
const BENCH_CONTAINER_H = 1920 * 0.4 - BENCH_PAD * 2;
// Actual image dimensions: 3000×902
const BENCH_IMG_NATURAL_W = 3000;
const BENCH_IMG_NATURAL_H = 902;
const BENCH_SCALE = BENCH_CONTAINER_H / BENCH_IMG_NATURAL_H;
const BENCH_IMG_W = Math.round(BENCH_IMG_NATURAL_W * BENCH_SCALE);
const BENCH_OVERFLOW = BENCH_IMG_W - BENCH_CONTAINER_W;

// Highlight ring — positioned in original image coordinates (pre-scale)
const HighlightRing: React.FC<{
  imgX: number; imgY: number; w: number; h: number;
  showStart: number; showEnd: number; color?: string;
}> = ({ imgX, imgY, w, h, showStart, showEnd, color = "#4285F4" }) => {
  const frame = useCurrentFrame();
  if (frame < showStart || frame > showEnd + 10) return null;
  const fadeIn = interpolate(frame, [showStart, showStart + 6], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [showEnd, showEnd + 10], [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pop = interpolate(frame, [showStart, showStart + 6], [1.2, 1.0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{
      position: "absolute",
      left: imgX * BENCH_SCALE, top: imgY * BENCH_SCALE,
      width: w * BENCH_SCALE, height: h * BENCH_SCALE,
      border: `3px solid ${color}`,
      borderRadius: 8,
      opacity: fadeIn * fadeOut,
      transform: `scale(${pop})`, transformOrigin: "center",
      pointerEvents: "none",
      boxShadow: `0 0 16px ${color}50`,
    }} />
  );
};

const ScrollingBenchmark: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();

  // Flow: hold → highlight Gemma 31B → remove → scroll to end → hold
  // Phase 1 (0-40%):  Hold at start. Gemma 4 31B column visible. Highlights appear.
  // Phase 2 (40-50%): Highlights fade out.
  // Phase 3 (50-90%): Scroll right to end of image.
  // Phase 4 (90-100%): Hold at end.
  const holdEnd = Math.floor(durationInFrames * 0.40);
  const scrollStart = Math.floor(durationInFrames * 0.50);
  const scrollEnd = Math.floor(durationInFrames * 0.90);

  const scrollX = interpolate(
    frame,
    [0, holdEnd, scrollStart, scrollEnd, durationInFrames],
    [0, 0, 0, -BENCH_OVERFLOW, -BENCH_OVERFLOW],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Highlight timing (frame numbers)
  const hlStart = 12;                     // Column highlight appears
  const hlEnd = holdEnd;                  // Highlight fades out when scroll begins

  return (
    <div style={{
      ...splitTopStyle, background: "#FFFFFF",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: BENCH_PAD,
    }}>
      <div style={{
        width: "100%", height: "100%",
        borderRadius: 16, overflow: "hidden",
        background: "#F0F2F5",
        boxShadow: "0 8px 32px rgba(0,0,0,0.15)",
      }}>
        <div style={{
          height: "100%",
          transform: `translateX(${scrollX}px)`,
          display: "flex", alignItems: "center",
          position: "relative",
        }}>
          <Img
            src={staticFile("benchmark-table.jpg")}
            style={{ height: "100%", objectFit: "contain", display: "block" }}
          />
          {/* Highlight entire Gemma 4 31B IT column (header + all data rows) */}
          <HighlightRing imgX={788} imgY={60} w={407} h={778} showStart={hlStart} showEnd={hlEnd} color="#4285F4" />
        </div>
      </div>
    </div>
  );
};

export const ReelComposition: React.FC<{ timeline: Timeline }> = ({ timeline }) => {
  return (
    <AbsoluteFill style={{ background: "#000000" }}>

      {/* ════════════ BACKGROUNDS ════════════ */}

      {/* Hook section — solid black (0–5.64s) */}
      <Sequence from={0} durationInFrames={toFrame(5.64)}>
        <AbsoluteFill style={{ background: "#000000" }} />
      </Sequence>

      {/* B-roll section — solid light (6.22–14.62s) with crossfade from black */}
      <Sequence from={toFrame(5.64)} durationInFrames={toFrame(9.0)}>
        <SeamCrossfade from={5.64} dur={10}>
          <AbsoluteFill style={{ background: "#F5F5F5" }} />
        </SeamCrossfade>
      </Sequence>

      {/* Avatar trust — dark blue (14.62–18.52) */}
      <Sequence from={toFrame(14.62)} durationInFrames={toFrame(3.9)}>
        <SeamCrossfade from={14.62} dur={8}>
          <AbsoluteFill style={{ background: "#1A1A2E" }} />
        </SeamCrossfade>
      </Sequence>

      {/* Dense architecture b-roll — light (18.52–22.14) */}
      <Sequence from={toFrame(17.94)} durationInFrames={toFrame(4.2)}>
        <SeamCrossfade from={17.94} dur={10}>
          <AbsoluteFill style={{ background: "#F5F5F5" }} />
        </SeamCrossfade>
      </Sequence>

      {/* Split-screen proof section — white (22.14–36.98) */}
      <Sequence from={toFrame(22.14)} durationInFrames={toFrame(14.84)}>
        <SeamCrossfade from={22.14} dur={8}>
          <AbsoluteFill style={{ background: "#FFFFFF" }} />
        </SeamCrossfade>
      </Sequence>

      {/* Avatar trust/recap — dark blue (36.98–42.86) */}
      <Sequence from={toFrame(36.98)} durationInFrames={toFrame(5.88)}>
        <SeamCrossfade from={36.98} dur={10}>
          <AbsoluteFill style={{ background: "#1A1A2E" }} />
        </SeamCrossfade>
      </Sequence>

      {/* CTA split — white (42.86–48.2) */}
      <Sequence from={toFrame(42.86)} durationInFrames={toFrame(5.34)}>
        <SeamCrossfade from={42.86} dur={10}>
          <AbsoluteFill style={{ background: "#FFFFFF" }} />
        </SeamCrossfade>
      </Sequence>

      {/* CTA close — very dark (48.2–end) */}
      <Sequence from={toFrame(48.2)} durationInFrames={toFrame(TOTAL - 48.2)}>
        <SeamCrossfade from={48.2} dur={8}>
          <AbsoluteFill style={{ background: "#0D0D1A" }} />
        </SeamCrossfade>
      </Sequence>

      {/* ════════════ AUDIO ════════════ */}

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

      {/* ════════════ B-ROLL VIDEOS (center-full) ════════════ */}

      {/* beat-01a: Google logo animation — hook intro (split-screen top 40%)
           Extended to 3.16s to hold last frame through gap → no black flash */}
      <Sequence from={0} durationInFrames={toFrame(3.16)}>
        <div style={splitTopStyle}>
          <OffthreadVideo
            src={staticFile("hook-clip-full.mp4")}
            muted
            style={{
              width: "100%", height: "100%",
              objectFit: "cover", objectPosition: "center",
            }}
          />
        </div>
      </Sequence>

      {/* beat-01b: ELO chart — hook proof (split-screen top 40%)
           Extended to 6.22s to hold through gap → no black flash before Gemma intro */}
      <Sequence from={toFrame(3.16)} durationInFrames={toFrame(6.22 - 3.16)} premountFor={5}>
        <div style={splitTopStyle}>
          <FramedImage
            src="elo-chart.png"
            splitScreen
            zoomMoments={[{ at: 0.0, x: 24, y: 18, scale: 2.0, holdFor: 2.4 }]}
          />
        </div>
      </Sequence>

      {/* beat-02: "What's new in Gemma 4" title card — center-full still image
           Uses objectFit: contain so full landscape text is readable in portrait frame
           Extended to 9.44s to hold through gap → no black flash, no Olivier appearing */}
      <Sequence from={toFrame(6.22)} durationInFrames={toFrame(9.44 - 6.22)} premountFor={10}>
        <AbsoluteFill style={{ zIndex: 12, background: "#000000", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Img
            src={staticFile("gemma4-title.jpg")}
            style={{
              width: "100%", height: "100%",
              objectFit: "contain", objectPosition: "center",
            }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* beat-03: Massive GPU b-roll — contain to show full landscape video */}
      <Sequence from={toFrame(9.44)} durationInFrames={toFrame(12.62 - 9.44)} premountFor={10}>
        <AbsoluteFill style={{ zIndex: 12, background: "#F5F5F5", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <OffthreadVideo
            src={staticFile("broll-massive-gpu.mp4")}
            muted
            style={{ width: "100%", objectFit: "contain" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* beat-04a: Device ecosystem b-roll — contain to show full landscape video */}
      <Sequence from={toFrame(12.62)} durationInFrames={toFrame(14.84 - 12.62)} premountFor={10}>
        <AbsoluteFill style={{ zIndex: 12, background: "#F5F5F5", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <OffthreadVideo
            src={staticFile("broll-device-ecosystem.mp4")}
            muted
            style={{ width: "100%", objectFit: "contain" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* beat-05: Dense Architecture b-roll — direct OffthreadVideo */}
      <Sequence from={toFrame(18.52)} durationInFrames={toFrame(22.58 - 18.52)} premountFor={10}>
        <AbsoluteFill style={{ zIndex: 12, background: "#F5F5F5" }}>
          <OffthreadVideo
            src={staticFile("broll-dense-architecture.mp4")}
            muted
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center" }}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ════════════ DEMO IMAGES (split-screen) ════════════ */}

      {/* beat-04b: Phone demo — extended to 16.22 to cover gap to avatar beat */}
      <Sequence from={toFrame(14.84)} durationInFrames={toFrame(16.22 - 14.84)}>
        <div style={splitTopStyle}>
          <FramedImage
            src="demo-phone.jpg"
            splitScreen
            zoomMoments={[{ at: 0.0, x: 65, y: 35, scale: 1.6, holdFor: 0.8 }]}
          />
        </div>
      </Sequence>

      {/* beat-06a + 06b: Benchmark table — scrolls horizontally to reveal all columns
           Image fills container height, scrolls left-to-right over both beats (22.58–30.0s)
           Dark device frame with rounded corners */}
      <Sequence from={toFrame(22.58)} durationInFrames={toFrame(30.0 - 22.58)}>
        <ScrollingBenchmark durationInFrames={toFrame(30.0 - 22.58)} />
      </Sequence>

      {/* beat-07a: HuggingFace — extended to 33.72 to cover gap */}
      <Sequence from={toFrame(30.0)} durationInFrames={toFrame(33.72 - 30.0)}>
        <div style={splitTopStyle}>
          <FramedImage
            src="huggingface.png"
            splitScreen
            zoomMoments={[{ at: 0.0, x: 35, y: 25, scale: 1.6, holdFor: 3.0 }]}
          />
        </div>
      </Sequence>

      {/* beat-07b: Ollama — extended to 37.66 to cover gap */}
      <Sequence from={toFrame(33.72)} durationInFrames={toFrame(37.66 - 33.72)}>
        <div style={splitTopStyle}>
          <FramedImage
            src="ollama.png"
            splitScreen
            zoomMoments={[{ at: 0.0, x: 40, y: 45, scale: 1.5, holdFor: 3.0 }]}
          />
        </div>
      </Sequence>

      {/* beat-10a: Ollama CTA — extended to 48.2 to cover gap */}
      <Sequence from={toFrame(43.64)} durationInFrames={toFrame(48.2 - 43.64)}>
        <div style={splitTopStyle}>
          <FramedImage
            src="ollama.png"
            splitScreen
            zoomMoments={[{ at: 0.0, x: 40, y: 25, scale: 1.4, holdFor: 4.0 }]}
          />
        </div>
      </Sequence>

      {/* ════════════ AVATAR ════════════ */}

      <AvatarVideo
        entries={timeline.lanes.avatar}
        hideRanges={centerFullRanges}
      />

      {/* ════════════ OVERLAYS ════════════ */}

      {/* beat-03: "MASSIVE SERVERS" on b-roll */}
      <Sequence from={toFrame(10.0)} durationInFrames={toFrame(1.98)}>
        <OverlayKeyword
          text="MASSIVE SERVERS"
          durationInFrames={toFrame(1.98)}
          color="#4285F4"
          fontSize={72}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-04c: "NEVER LEAVES" on avatar face */}
      <Sequence from={toFrame(16.5)} durationInFrames={toFrame(1.44)}>
        <OverlayKeyword
          text="NEVER LEAVES"
          durationInFrames={toFrame(1.44)}
          color="#FFFFFF"
          fontSize={80}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-05: "STRIPPED DOWN" on b-roll */}
      <Sequence from={toFrame(19.5)} durationInFrames={toFrame(2.64)}>
        <OverlayKeyword
          text="STRIPPED DOWN"
          durationInFrames={toFrame(2.64)}
          color="#EA4335"
          fontSize={80}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-06a: "13x" hero stat on benchmark */}
      <Sequence from={toFrame(23.0)} durationInFrames={toFrame(3.32)}>
        <OverlayKeyword
          text="13x"
          durationInFrames={toFrame(3.32)}
          color="#4285F4"
          fontSize={96}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-07a: "OPEN SOURCE" badge on HuggingFace */}
      <Sequence from={toFrame(31.5)} durationInFrames={toFrame(1.62)}>
        <AbsoluteFill style={{ display: "flex", alignItems: "flex-start", justifyContent: "center", paddingTop: 80, zIndex: 20 }}>
          <BadgePopup
            text="OPEN SOURCE"
            durationInFrames={toFrame(1.62)}
            color="#34A853"
            size="large"
          />
        </AbsoluteFill>
      </Sequence>

      {/* beat-08: "400M+" on avatar face */}
      <Sequence from={toFrame(38.0)} durationInFrames={toFrame(1.58)}>
        <OverlayKeyword
          text="400M+"
          durationInFrames={toFrame(1.58)}
          color="#4285F4"
          fontSize={110}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-09: "RUN AND OWN" on avatar face */}
      <Sequence from={toFrame(41.0)} durationInFrames={toFrame(1.86)}>
        <OverlayKeyword
          text="RUN AND OWN"
          durationInFrames={toFrame(1.86)}
          color="#FFFFFF"
          fontSize={72}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* beat-10b: "FOLLOW" on avatar face — dark bg */}
      <Sequence from={toFrame(49.0)} durationInFrames={toFrame(1.88)}>
        <OverlayKeyword
          text="FOLLOW"
          durationInFrames={toFrame(1.88)}
          color="#4285F4"
          fontSize={96}
          position="center"
          shadowStrength="strong"
        />
      </Sequence>

      {/* ════════════ CAPTIONS ════════════ */}

      {timeline.lanes.captions.map((cap, i) => (
        <Sequence
          key={`cap-${i}`}
          from={toFrame(cap.start)}
          durationInFrames={Math.max(1, toFrame(cap.end - cap.start))}
        >
          <Caption text={cap.text!} durationInFrames={Math.max(1, toFrame(cap.end - cap.start))} />
        </Sequence>
      ))}

      {/* ════════════ NOISE (subtle film grain) ════════════ */}

      <NoiseOverlay opacity={0.03} />

    </AbsoluteFill>
  );
};
