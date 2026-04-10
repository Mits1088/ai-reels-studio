import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
  random,
} from "remotion";
import type { TransitionPreset } from "../../types";

function exitOpacityCalc(frame: number, dur: number, preset: TransitionPreset): number {
  // hard-cut or exitDur 0 — no fade, just instant (handled by Sequence end)
  if (preset.exit === "hard-cut" || preset.exitDur <= 0) return 1;
  const fadeStart = Math.max(0, dur - 1 - preset.exitDur);
  const fadeEnd = dur - 1;
  if (fadeStart >= fadeEnd) return 1;
  return interpolate(
    frame,
    [fadeStart, fadeEnd],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
}

const KenBurnsWrap: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  const panX = Math.sin(frame * 0.005) * 6;
  return (
    <div style={{ width: "100%", height: "100%", transform: `scale(${drift}) translateX(${panX}px)` }}>
      {children}
    </div>
  );
};

export const TransitionWrapper: React.FC<{
  children: React.ReactNode;
  durationInFrames: number;
  preset: TransitionPreset;
}> = ({ children, durationInFrames, preset }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let enterOpacity = 1;
  let enterTransform = "";
  let clipPath = "";

  switch (preset.enter) {
    case "punch": {
      const t = interpolate(frame, [0, 1, preset.enterDur], [1.15, 0.98, 1.0], {
        extrapolateLeft: "clamp", extrapolateRight: "clamp",
      });
      enterTransform = `scale(${t})`;
      enterOpacity = frame < 1 ? 0 : 1;
      break;
    }
    case "slide-up": {
      const s = spring({ frame, fps, config: { damping: 18, stiffness: 200 } });
      enterTransform = `translateY(${interpolate(s, [0, 1], [60, 0])}px)`;
      enterOpacity = s;
      break;
    }
    case "slide-left": {
      const s = spring({ frame, fps, config: { damping: 18, stiffness: 200 } });
      enterTransform = `translateX(${interpolate(s, [0, 1], [100, 0])}px)`;
      enterOpacity = s;
      break;
    }
    case "wipe-up": {
      const progress = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
      });
      const clipBottom = interpolate(progress, [0, 1], [100, 0]);
      return (
        <div style={{
          width: "100%", height: "100%",
          clipPath: `inset(0 0 ${clipBottom}% 0)`,
          opacity: exitOpacityCalc(frame, durationInFrames, preset),
        }}>
          {preset.kenBurns ? <KenBurnsWrap dur={durationInFrames}>{children}</KenBurnsWrap> : children}
        </div>
      );
    }
    case "zoom-in": {
      const t = interpolate(frame, [0, preset.enterDur], [1.12, 1.0], {
        extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
      });
      enterTransform = `scale(${t})`;
      enterOpacity = interpolate(frame, [0, 2], [0, 1], { extrapolateRight: "clamp" });
      break;
    }
    case "scale-pop": {
      const s = spring({ frame, fps, config: { damping: 12, stiffness: 220, mass: 0.7 } });
      enterTransform = `scale(${interpolate(s, [0, 1], [0.7, 1.0])})`;
      enterOpacity = interpolate(frame, [0, 2], [0, 1], { extrapolateRight: "clamp" });
      break;
    }
    case "glitch": {
      if (frame < preset.enterDur) {
        const offsetX = (random(`glx-${frame}`) - 0.5) * 12;
        const offsetY = (random(`gly-${frame}`) - 0.5) * 6;
        enterTransform = `translate(${offsetX}px, ${offsetY}px)`;
        enterOpacity = frame < 1 ? 0.7 : 1;
      }
      break;
    }

    // ── Smooth transitions (no blur — transform + opacity only) ──

    case "zoom-through": {
      // Fast scale-down from oversized — feels like diving in
      const progress = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
      });
      enterTransform = `scale(${interpolate(progress, [0, 1], [1.25, 1.0])})`;
      enterOpacity = interpolate(progress, [0, 0.15, 1], [0, 1, 1]);
      break;
    }
    case "blur-dissolve": {
      // Smooth fade with slight scale settle — cinematic without blur
      const progress = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp", easing: Easing.bezier(0.25, 0.1, 0.25, 1),
      });
      enterOpacity = interpolate(progress, [0, 0.3, 1], [0, 0.7, 1]);
      enterTransform = `scale(${interpolate(progress, [0, 1], [1.03, 1.0])})`;
      break;
    }
    case "luminance-sweep": {
      // Diagonal clip reveal — light wipe feel without actual filter
      const progress = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
      });
      const sweepPos = interpolate(progress, [0, 1], [-20, 120]);
      if (progress < 0.95) {
        clipPath = `polygon(${sweepPos - 30}% 0%, ${sweepPos + 20}% 0%, ${sweepPos - 10}% 100%, ${sweepPos - 60}% 100%)`;
      }
      enterOpacity = 1;
      break;
    }
    case "iris-reveal": {
      // Circle expands from center
      const progress = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
      });
      clipPath = progress < 0.98 ? `circle(${interpolate(progress, [0, 1], [0, 75])}% at 50% 50%)` : "";
      enterOpacity = 1;
      break;
    }
    case "whip-pan": {
      // Fast slide from side — no blur, just speed + overshoot
      const s = spring({ frame, fps, config: { damping: 14, stiffness: 250, mass: 0.6 } });
      enterTransform = `translateX(${interpolate(s, [0, 1], [300, 0])}px)`;
      enterOpacity = interpolate(frame, [0, 1], [0, 1], { extrapolateRight: "clamp" });
      break;
    }
    case "smooth-push": {
      // Spring push from right edge
      const s = spring({ frame, fps, config: { damping: 15, stiffness: 160, mass: 0.8 } });
      enterTransform = `translateX(${interpolate(s, [0, 1], [1080, 0])}px)`;
      enterOpacity = 1;
      break;
    }

    // ── Editorial-authority presets ──

    case "hard-cut": {
      // Instant appear — no animation
      enterOpacity = 1;
      break;
    }
    case "scale-pop-overshoot": {
      // Scale 0.85 → 1.03 → 1.0 with overshoot settle (editorial title cards)
      const s = spring({ frame, fps, config: { damping: 12, stiffness: 300, mass: 0.6 } });
      enterTransform = `scale(${interpolate(s, [0, 1], [0.85, 1.0])})`;
      enterOpacity = interpolate(frame, [0, 2], [0, 1], { extrapolateRight: "clamp" });
      break;
    }
    case "flash-reset": {
      // 2-frame white flash then reveal — used as section divider
      // The flash itself is handled by FlashReset component; this preset just does instant appear
      enterOpacity = 1;
      break;
    }
    case "slide-stack": {
      // Slide from right with rotation — numbered card stacking
      const s = spring({ frame, fps, config: { damping: 12, stiffness: 160, mass: 0.7 } });
      const tx = interpolate(s, [0, 1], [400, 0]);
      const rot = interpolate(s, [0, 1], [8, 0]);
      enterTransform = `translateX(${tx}px) rotate(${rot}deg)`;
      enterOpacity = interpolate(frame, [0, 2], [0, 1], { extrapolateRight: "clamp" });
      break;
    }
    default: {
      enterOpacity = interpolate(frame, [0, preset.enterDur], [0, 1], {
        extrapolateRight: "clamp",
      });
      break;
    }
  }

  // ── Exit animations ──

  const exitOpacity = exitOpacityCalc(frame, durationInFrames, preset);
  let exitTransform = "";

  const exitStart = Math.max(0, durationInFrames - preset.exitDur - 1);
  const exitEnd = durationInFrames - 1;
  if (preset.exit !== "hard-cut" && preset.exitDur > 0 && exitStart < exitEnd && frame > exitStart) {
    const exitProgress = interpolate(
      frame,
      [exitStart, exitEnd],
      [0, 1],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );

    switch (preset.exit) {
      case "punch-out":
        exitTransform = `scale(${interpolate(exitProgress, [0, 1], [1.0, 1.12])})`;
        break;
      case "slide-down":
        exitTransform = `translateY(${interpolate(exitProgress, [0, 1], [0, 50])}px)`;
        break;
      case "slide-right":
        exitTransform = `translateX(${interpolate(exitProgress, [0, 1], [0, 80])}px)`;
        break;
      case "scale-down":
        exitTransform = `scale(${interpolate(exitProgress, [0, 1], [1.0, 0.88])})`;
        break;
      case "zoom-through-out":
        // Scale up and fade — fast zoom past
        exitTransform = `scale(${interpolate(exitProgress, [0, 1], [1.0, 1.25])})`;
        break;
      case "blur-out":
        // Scale up slightly + fade (no actual blur)
        exitTransform = `scale(${interpolate(exitProgress, [0, 1], [1.0, 1.04])})`;
        break;
      case "whip-out":
        // Fast slide out left
        exitTransform = `translateX(${interpolate(exitProgress, [0, 1], [0, -400])}px)`;
        break;
      case "iris-close":
        clipPath = `circle(${interpolate(exitProgress, [0, 1], [75, 0])}% at 50% 50%)`;
        break;
      // hard-cut is filtered out above — never reaches this switch
      default:
        break;
    }
  }

  // ── Ken Burns ──
  let kenBurnsTransform = "";
  if (preset.kenBurns) {
    const drift = interpolate(frame, [0, durationInFrames], [1.0, 1.06], { extrapolateRight: "clamp" });
    const panX = Math.sin(frame * 0.005) * 6;
    kenBurnsTransform = `scale(${drift}) translateX(${panX}px)`;
  }

  const combinedTransform = [enterTransform, exitTransform, kenBurnsTransform].filter(Boolean).join(" ");
  const combinedOpacity = enterOpacity * exitOpacity;

  return (
    <div style={{
      width: "100%", height: "100%",
      transform: combinedTransform || undefined,
      opacity: combinedOpacity,
      clipPath: clipPath || undefined,
    }}>
      {children}
    </div>
  );
};
