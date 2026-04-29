import React from "react";
import { AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile } from "remotion";
import { EndScreen } from "./components/effects/EndScreen";
import { HeroTextCard } from "./components/effects/HeroTextCard";
import { LowerThird } from "./components/effects/LowerThird";
import { ProgressSteps } from "./components/effects/ProgressSteps";
import { StatCounter } from "./components/effects/StatCounter";
import { SubscribeCTA } from "./components/effects/SubscribeCTA";

const FPS = 30;

// Seconds → frames
const f = (sec: number) => Math.round(sec * FPS);

// Total duration: 17:37.508 from Whisper transcript
export const YT_TOTAL_FRAMES = Math.ceil(1057.508 * FPS); // 31726

// Opaque B-roll clip — replaces recording in CapCut during this window
const BRoll: React.FC<{ src: string }> = ({ src }) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <OffthreadVideo
      src={staticFile(src)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
      muted
    />
  </AbsoluteFill>
);

/**
 * YouTubeOverlay — Single 17:37 composition with every motion graphic + SFX
 * sequenced at exact transcript timestamps.
 *
 * Render as transparent WebM:
 *   npx remotion render YT-FullOverlay out/yt/full-overlay.webm --codec=vp8
 *
 * In CapCut: V1 = recording (audio on), V2 = full-overlay.webm (audio on for SFX)
 * Transparent areas let the recording show through.
 * B-roll windows are opaque and replace the recording.
 */
export const YouTubeOverlay: React.FC = () => (
  <AbsoluteFill style={{ background: "transparent" }}>

    {/* ── B-ROLL (rendered first — overlays have zIndex: 55 and paint on top) ── */}

    {/* 0:05–0:12 (7s) — intro b-roll: person typing on laptop */}
    <Sequence from={f(5)} durationInFrames={210}>
      <Audio src={staticFile("sfx-whoosh-short.mp3")} volume={0.6} />
      <BRoll src="yt-broll-intro.mp4" />
    </Sequence>

    {/* 2:12–2:22 (10s) — chat b-roll: typing, follow-up emails */}
    <Sequence from={f(132)} durationInFrames={300}>
      <Audio src={staticFile("sfx-whoosh-short.mp3")} volume={0.6} />
      <BRoll src="yt-broll-chat.mp4" />
    </Sequence>

    {/* 6:15–6:25 (10s) — dispatch b-roll: professional walking with phone */}
    <Sequence from={f(375)} durationInFrames={300}>
      <Audio src={staticFile("sfx-whoosh-short.mp3")} volume={0.6} />
      <BRoll src="yt-broll-dispatch.mp4" />
    </Sequence>

    {/* 7:50–8:00 (10s) — code b-roll: dark terminal screen */}
    <Sequence from={f(470)} durationInFrames={300}>
      <Audio src={staticFile("sfx-whoosh-short.mp3")} volume={0.6} />
      <BRoll src="yt-broll-code.mp4" />
    </Sequence>

    {/* ── OVERLAYS (transparent — recording / b-roll shows behind) ── */}

    {/* 0:00 — "15%" count-up hook stat */}
    <Sequence from={f(0)} durationInFrames={150}>
      <Audio src={staticFile("sfx-impact-bass.mp3")} volume={0.9} />
      <StatCounter
        value={15}
        startValue={0}
        suffix="%"
        label="of Claude's potential"
        color="#D97757"
        fontSize={220}
        labelFontSize={56}
        durationInFrames={150}
      />
    </Sequence>

    {/* 0:30 — Presenter badge */}
    <Sequence from={f(30)} durationInFrames={120}>
      <Audio src={staticFile("sfx-soft-slide.mp3")} volume={0.7} />
      <LowerThird
        title="Mits"
        subtitle="AI Tools for Business"
        accentColor="#D97757"
        titleFontSize={42}
        subtitleFontSize={28}
        durationInFrames={120}
        position="bottom-left"
      />
    </Sequence>

    {/* 1:19 — "4 Modes / + 2 Add-ons" framework reveal */}
    <Sequence from={f(79)} durationInFrames={120}>
      <Audio src={staticFile("sfx-impact-bass.mp3")} volume={0.8} />
      <HeroTextCard
        text="4 Modes"
        subtitle="+ 2 Add-ons"
        backgroundColor="rgba(15, 15, 15, 0.88)"
        textColor="#FFFFFF"
        fontSize={140}
        subtitleColor="#D97757"
        subtitleFontSize={90}
        withOvershoot={true}
        durationInFrames={120}
      />
    </Sequence>

    {/* 1:20 — All 6 features staggered reveal (8s) */}
    <Sequence from={f(80)} durationInFrames={240}>
      <Audio src={staticFile("sfx-subtle-transition.mp3")} volume={0.5} />
      <ProgressSteps
        steps={[
          { label: "Claude Chat", sublabel: "Quick questions, writing, research" },
          { label: "Co-Work", sublabel: "Work with files on your computer" },
          { label: "Dispatch", sublabel: "Hand off tasks from your phone" },
          { label: "Claude Code", sublabel: "Build tools that run on your computer" },
          { label: "Plugins", sublabel: "Connect Claude to your tools" },
          { label: "Skills", sublabel: "Teach Claude how you want things done" },
        ]}
        accentColor="#D97757"
        staggerFrames={20}
        durationInFrames={240}
      />
    </Sequence>

    {/* 1:33 — Subscribe bell (mid-intro, just before features begin) */}
    <Sequence from={f(93)} durationInFrames={150}>
      <Audio src={staticFile("sfx-notification.mp3")} volume={0.8} />
      <SubscribeCTA
        channelName="Mits"
        position="bottom-center"
        accentColor="#FF0000"
        durationInFrames={150}
      />
    </Sequence>

    {/* 1:36 — Feature badge: 1 of 6 / Claude Chat */}
    <Sequence from={f(96)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="1 of 6"
        subtitle="Claude Chat"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/chat.svg"
      />
    </Sequence>

    {/* 2:53 — Feature badge: 2 of 6 / Claude Co-Work */}
    <Sequence from={f(173)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="2 of 6"
        subtitle="Claude Co-Work"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/cowork.svg"
      />
    </Sequence>

    {/* 6:07 — Feature badge: 3 of 6 / Dispatch */}
    <Sequence from={f(367)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="3 of 6"
        subtitle="Dispatch"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/dispatch.svg"
      />
    </Sequence>

    {/* 7:49 — Feature badge: 4 of 6 / Claude Code
        Overlaps BRoll-Code (7:50) by 4 seconds — badge floats on top of the b-roll. */}
    <Sequence from={f(469)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="4 of 6"
        subtitle="Claude Code"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/code.svg"
      />
    </Sequence>

    {/* 11:04 — Feature badge: 5 of 6 / Plugins */}
    <Sequence from={f(664)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="5 of 6"
        subtitle="Plugins"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/plugins.svg"
      />
    </Sequence>

    {/* 14:41 — Feature badge: 6 of 6 / Skills */}
    <Sequence from={f(881)} durationInFrames={150}>
      <Audio src={staticFile("sfx-pop.mp3")} volume={0.7} />
      <LowerThird
        title="6 of 6"
        subtitle="Skills"
        accentColor="#D97757"
        titleFontSize={36}
        subtitleFontSize={52}
        durationInFrames={150}
        position="bottom-left"
        logoSrc="brands/features/skills.svg"
      />
    </Sequence>

    {/* 16:21 — All 6 features recap (faster stagger, 10s hold) */}
    <Sequence from={f(981)} durationInFrames={300}>
      <Audio src={staticFile("sfx-subtle-transition.mp3")} volume={0.5} />
      <ProgressSteps
        steps={[
          { label: "Claude Chat", sublabel: "Quick questions, writing, research" },
          { label: "Co-Work", sublabel: "Work with files on your computer" },
          { label: "Dispatch", sublabel: "Hand off tasks from your phone" },
          { label: "Claude Code", sublabel: "Build tools that run on your computer" },
          { label: "Plugins", sublabel: "Connect Claude to your tools" },
          { label: "Skills", sublabel: "Teach Claude how you want things done" },
        ]}
        accentColor="#D97757"
        staggerFrames={10}
        durationInFrames={300}
      />
    </Sequence>

    {/* 17:07 — Subscribe bell (end, "please do subscribe") */}
    <Sequence from={f(1027)} durationInFrames={150}>
      <Audio src={staticFile("sfx-notification.mp3")} volume={0.8} />
      <SubscribeCTA
        channelName="Mits"
        position="bottom-center"
        accentColor="#FF0000"
        durationInFrames={150}
      />
    </Sequence>

    {/* 17:22 — End screen (last 15s of video) */}
    <Sequence from={f(1042)} durationInFrames={450}>
      <Audio src={staticFile("sfx-cinematic-whoosh.mp3")} volume={0.7} />
      <EndScreen
        channelName="Mits"
        accentColor="#D97757"
        backgroundColor="rgba(0, 0, 0, 0.88)"
        leftTitle="Watch Next"
        rightTitle="Popular"
        durationInFrames={450}
      />
    </Sequence>

  </AbsoluteFill>
);
