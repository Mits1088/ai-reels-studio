import React from "react";
import { AbsoluteFill, Composition, Folder, OffthreadVideo, staticFile } from "remotion";
import { GenericReelComposition } from "./GenericReelComposition";
import type { Timeline } from "./types";
import timelineData from "../public/timeline.json";
import timelineCinematic from "../public/timeline-cinematic.json";
import { LowerThird } from "./components/effects/LowerThird";
import { ProgressSteps } from "./components/effects/ProgressSteps";
import { SubscribeCTA } from "./components/effects/SubscribeCTA";
import { EndScreen } from "./components/effects/EndScreen";
import { StatCounter } from "./components/effects/StatCounter";
import { HeroTextCard } from "./components/effects/HeroTextCard";
import { YouTubeOverlay, YT_TOTAL_FRAMES } from "./YouTubeOverlay";

const FPS = 30;
const reelFrames = Math.ceil(timelineData.total_duration * FPS);
const reelFramesCinematic = Math.ceil(timelineCinematic.total_duration * FPS);

// Simple full-frame B-roll clip component (opaque — replaces recording in CapCut)
const BRollClip: React.FC<{ src: string; startFrom?: number }> = ({ src, startFrom = 0 }) => (
  <AbsoluteFill style={{ background: "#000" }}>
    <OffthreadVideo
      src={staticFile(src)}
      startFrom={startFrom * FPS}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
      muted
    />
  </AbsoluteFill>
);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Reels">
        {/* Editorial — hard cuts + stat punches */}
        <Composition
          id="ReelComposition"
          component={GenericReelComposition}
          durationInFrames={reelFrames}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            timeline: timelineData as unknown as Timeline,
          }}
        />
        {/* Cinematic — slide-up reveals, smooth transitions */}
        <Composition
          id="ReelCompositionCinematic"
          component={GenericReelComposition}
          durationInFrames={reelFramesCinematic}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            timeline: timelineCinematic as unknown as Timeline,
          }}
        />
      </Folder>

      <Folder name="YouTube-Claude-6-Features">

        {/* ── SINGLE OVERLAY COMPOSITION — render this one for CapCut assembly ──
            npx remotion render YT-FullOverlay out/yt/full-overlay.webm --codec=vp8
            Drop full-overlay.webm on V2 above the recording in CapCut.
            ──────────────────────────────────────────────────────────────────── */}
        <Composition
          id="YT-FullOverlay"
          component={YouTubeOverlay}
          durationInFrames={YT_TOTAL_FRAMES}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{}}
        />

        {/* ── OVERLAYS (transparent WebM) ─────────────────────────────────────────
            Render with: npx remotion render <ID> out/yt/<name>.webm --codec=vp8
            These are TRANSPARENT layers dropped on top of recording in CapCut.
            ──────────────────────────────────────────────────────────────────── */}

        {/* 0:00 — Hook: "15% of what it can do" — count-up stat */}
        <Composition
          id="YT-HookStat"
          component={StatCounter}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            value: 15,
            startValue: 0,
            suffix: "%",
            label: "of Claude's potential",
            color: "#D97757",
            fontSize: 220,
            labelFontSize: 56,
            durationInFrames: 150,
          }}
        />

        {/* 0:30 — "My name is Mitz" — presenter name tag */}
        <Composition
          id="YT-LowerThird-Mits"
          component={LowerThird}
          durationInFrames={120}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "Mits",
            subtitle: "AI Tools for Business",
            accentColor: "#D97757",
            titleFontSize: 42,
            subtitleFontSize: 28,
            durationInFrames: 120,
            position: "bottom-left",
          }}
        />

        {/* 1:19 — "four different ways... two add-ons" — framework reveal */}
        <Composition
          id="YT-Framework"
          component={HeroTextCard}
          durationInFrames={120}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            text: "4 Modes",
            subtitle: "+ 2 Add-ons",
            backgroundColor: "rgba(15, 15, 15, 0.88)",
            textColor: "#FFFFFF",
            fontSize: 140,
            subtitleColor: "#D97757",
            subtitleFontSize: 90,
            withOvershoot: true,
            durationInFrames: 120,
          }}
        />

        {/* 1:20 — All 6 features listed (staggered reveal, 8s) */}
        <Composition
          id="YT-FeatureMap-Overview"
          component={ProgressSteps}
          durationInFrames={240}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            steps: [
              { label: "Claude Chat", sublabel: "Quick questions, writing, research" },
              { label: "Co-Work", sublabel: "Work with files on your computer" },
              { label: "Dispatch", sublabel: "Hand off tasks from your phone" },
              { label: "Claude Code", sublabel: "Build tools that run on your computer" },
              { label: "Plugins", sublabel: "Connect Claude to your tools" },
              { label: "Skills", sublabel: "Teach Claude how you want things done" },
            ],
            accentColor: "#D97757",
            staggerFrames: 20,
            durationInFrames: 240,
          }}
        />

        {/* 1:33 — Mid-intro subscribe prompt (before features begin) */}
        <Composition
          id="YT-SubscribeCTA-Mid"
          component={SubscribeCTA}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            channelName: "Mits",
            position: "bottom-center",
            accentColor: "#FF0000",
            durationInFrames: 150,
          }}
        />

        {/* ── FEATURE BADGES — one per section ──────────────────────────────────── */}

        {/* 1:36 — "number one is Claude Chat" */}
        <Composition
          id="YT-Feature-1-Chat"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "1 of 6",
            subtitle: "Claude Chat",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/chat.svg",
          }}
        />

        {/* 2:53 — "Number two is Claude Cowork" */}
        <Composition
          id="YT-Feature-2-CoWork"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "2 of 6",
            subtitle: "Claude Co-Work",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/cowork.svg",
          }}
        />

        {/* 6:07 — "Number three is dispatch" */}
        <Composition
          id="YT-Feature-3-Dispatch"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "3 of 6",
            subtitle: "Dispatch",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/dispatch.svg",
          }}
        />

        {/* 7:49 — "Number four is Claude code" */}
        <Composition
          id="YT-Feature-4-Code"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "4 of 6",
            subtitle: "Claude Code",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/code.svg",
          }}
        />

        {/* 11:04 — "Next is plugins" */}
        <Composition
          id="YT-Feature-5-Plugins"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "5 of 6",
            subtitle: "Plugins",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/plugins.svg",
          }}
        />

        {/* 14:41 — "number six is skills" */}
        <Composition
          id="YT-Feature-6-Skills"
          component={LowerThird}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            title: "6 of 6",
            subtitle: "Skills",
            accentColor: "#D97757",
            titleFontSize: 36,
            subtitleFontSize: 52,
            durationInFrames: 150,
            position: "bottom-left",
            logoSrc: "brands/features/skills.svg",
          }}
        />

        {/* 16:21 — "right here's the full map" — faster recap of all 6 */}
        <Composition
          id="YT-FeatureMap-Summary"
          component={ProgressSteps}
          durationInFrames={300}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            steps: [
              { label: "Claude Chat", sublabel: "Quick questions, writing, research" },
              { label: "Co-Work", sublabel: "Work with files on your computer" },
              { label: "Dispatch", sublabel: "Hand off tasks from your phone" },
              { label: "Claude Code", sublabel: "Build tools that run on your computer" },
              { label: "Plugins", sublabel: "Connect Claude to your tools" },
              { label: "Skills", sublabel: "Teach Claude how you want things done" },
            ],
            accentColor: "#D97757",
            staggerFrames: 10,
            durationInFrames: 300,
          }}
        />

        {/* 17:07 — "please do subscribe" — end subscribe prompt */}
        <Composition
          id="YT-SubscribeCTA"
          component={SubscribeCTA}
          durationInFrames={150}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            channelName: "Mits",
            position: "bottom-center",
            accentColor: "#FF0000",
            durationInFrames: 150,
          }}
        />

        {/* 17:22 — End screen (last 15s) */}
        <Composition
          id="YT-EndScreen"
          component={EndScreen}
          durationInFrames={450}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            channelName: "Mits",
            accentColor: "#D97757",
            backgroundColor: "rgba(0, 0, 0, 0.88)",
            leftTitle: "Watch Next",
            rightTitle: "Popular",
            durationInFrames: 450,
          }}
        />

        {/* ── B-ROLL CLIPS (opaque mp4) ──────────────────────────────────────────
            Render with: npx remotion render <ID> out/yt/<name>.mp4
            These REPLACE the recording in CapCut — cut your recording at the
            timestamp listed, insert this clip on the same layer.
            ──────────────────────────────────────────────────────────────────── */}

        {/* 0:05 — 0:12 (7s) — "they open the chat, they ask a question"
            Person typing on laptop. Cuts over the intro concept statement. */}
        <Composition
          id="YT-BRoll-Intro"
          component={BRollClip}
          durationInFrames={210}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{ src: "yt-broll-intro.mp4", startFrom: 0 }}
        />

        {/* 2:12 — 2:22 (10s) — "drafting a follow-up email to proposals"
            Person typing on laptop. Cuts during the Claude Chat use-case list. */}
        <Composition
          id="YT-BRoll-Chat"
          component={BRollClip}
          durationInFrames={300}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{ src: "yt-broll-chat.mp4", startFrom: 0 }}
        />

        {/* 6:15 — 6:25 (10s) — "on the way home from work, full day meetings"
            Professional walking while on phone. Dispatch section scene-setter. */}
        <Composition
          id="YT-BRoll-Dispatch"
          component={BRollClip}
          durationInFrames={300}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{ src: "yt-broll-dispatch.mp4", startFrom: 0 }}
        />

        {/* 7:50 — 8:00 (10s) — "building actual software, real working tools"
            Code running on dark terminal screen. Claude Code intro moment. */}
        <Composition
          id="YT-BRoll-Code"
          component={BRollClip}
          durationInFrames={300}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{ src: "yt-broll-code.mp4", startFrom: 0 }}
        />

      </Folder>
    </>
  );
};
