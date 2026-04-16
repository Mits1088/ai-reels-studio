/**
 * GlitchText — vendored from clippkit (MIT)
 * Source: https://github.com/reactvideoeditor/clippkit
 *         apps/docs/registry/default/components/glitch-text.tsx
 *
 * Adapted for the AI Reels Studio pipeline:
 *  - Named export instead of default
 *  - Replaced Math.random() with Remotion's deterministic random() for
 *    reproducible renders
 *  - Theme defaults (coral / dark)
 *  - Wraps in AbsoluteFill so it works as an OVERLAY_REGISTRY entry
 *
 * Use it for high-impact emphasis moments — single-word reveals, dramatic
 * payoffs (e.g. "GONE"), or pain-elimination beats where the text needs to
 * feel destabilized. Pair with FlashReset for the strongest hit.
 */
import React from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";

interface GlitchTextProps {
  text?: string;
  textColor?: string;
  glitchTextColor1?: string;
  glitchTextColor2?: string;
  fontSize?: string;
  fontFamily?: string;
  fontWeight?: number | string;
  glitchStrength?: number;
  glitchSpeed?: number;
  /** When set (0-1), glitch only fires occasionally per frame instead of continuous. */
  sporadicGlitchChance?: number;
  durationInFrames?: number;
}

export const GlitchText: React.FC<GlitchTextProps> = ({
  text = "GLITCH",
  textColor = "#FFFFFF",
  glitchTextColor1 = "#D97757",
  glitchTextColor2 = "#00E5FF",
  fontSize = "12rem",
  fontFamily = "'Inter', system-ui, -apple-system, sans-serif",
  fontWeight = 900,
  glitchStrength = 14,
  glitchSpeed = 5,
  sporadicGlitchChance,
}) => {
  const frame = useCurrentFrame();

  let currentGlitchIntensity = 0;
  let currentRgbOffset = 0;

  if (sporadicGlitchChance !== undefined && sporadicGlitchChance > 0) {
    // Use deterministic random seeded by frame so renders are reproducible.
    if (random(`glitch-${frame}`) < sporadicGlitchChance) {
      if (
        frame % Math.max(1, Math.floor(glitchSpeed)) === 0 ||
        glitchSpeed < 1
      ) {
        currentGlitchIntensity =
          (random(`intensity-${frame}`) - 0.5) * 2 * glitchStrength;
        currentRgbOffset =
          (random(`rgb-${frame}`) - 0.5) * 2 * (glitchStrength / 1.5);
      }
    }
  } else {
    // Continuous sine-wave glitch
    currentGlitchIntensity = Math.sin(frame / glitchSpeed) * glitchStrength;
    currentRgbOffset =
      Math.sin(frame / (glitchSpeed / 2)) * (glitchStrength / 2);
  }

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          fontSize,
          fontWeight,
          fontFamily,
          letterSpacing: -2,
        }}
      >
        <div
          style={{
            position: "absolute",
            color: glitchTextColor1,
            transform: `translate(${currentRgbOffset}px, ${currentGlitchIntensity}px)`,
            mixBlendMode: "screen",
            opacity: 0.7,
            top: 0,
            left: 0,
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </div>
        <div
          style={{
            position: "absolute",
            color: glitchTextColor2,
            transform: `translate(${-currentRgbOffset}px, ${-currentGlitchIntensity}px)`,
            mixBlendMode: "screen",
            opacity: 0.7,
            top: 0,
            left: 0,
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </div>
        <div style={{ color: textColor, opacity: 0.95, whiteSpace: "nowrap" }}>
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
