/**
 * CircularWaveform — vendored from clippkit (MIT)
 * Source: https://github.com/reactvideoeditor/clippkit
 *         apps/docs/registry/default/components/circular-waveform.tsx
 *
 * Adapted for the AI Reels Studio pipeline:
 *  - Named export instead of default
 *  - Theme defaults
 *  - Wraps in AbsoluteFill for OVERLAY_REGISTRY use
 *
 * Use it as a centered audio orb visualization — alternative to BarWaveform
 * when the bottom-of-frame strip doesn't fit. Works well as the focal
 * visual for an audio-only beat.
 */
import React from "react";
import {
  MediaUtilsAudioData,
  visualizeAudioWaveform,
} from "@remotion/media-utils";
import {
  AbsoluteFill,
  random,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface CircularWaveformProps {
  audioData?: MediaUtilsAudioData | null;
  barCount?: number;
  barWidth?: number;
  barColor?: string;
  waveAmplitude?: number;
  radius?: number;
  centerOffset?: { x?: number; y?: number };
  barMinHeight?: number;
  rotationOffset?: number;
  growOutwardsOnly?: boolean;
  durationInFrames?: number;
}

export const CircularWaveform: React.FC<CircularWaveformProps> = ({
  audioData,
  barCount = 60,
  barWidth = 5,
  barColor = "#D97757",
  waveAmplitude = 100,
  radius = 200,
  centerOffset = { x: 0, y: 0 },
  barMinHeight = 6,
  rotationOffset = 0,
  growOutwardsOnly = true,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const centerX = width / 2 + (centerOffset.x ?? 0);
  const centerY = height / 2 + (centerOffset.y ?? 0);

  const waveformSamples = audioData
    ? visualizeAudioWaveform({
        fps,
        frame,
        audioData,
        numberOfSamples: barCount,
        windowInSeconds: 1 / fps,
      })
    : Array(barCount)
        .fill(0)
        .map((_, i) => {
          const seed = `circwave-${i}`;
          return (
            Math.max(
              0.1,
              Math.abs(
                Math.sin(frame / 10 + i / (barCount / (2 * Math.PI))),
              ) +
                random(seed) * 0.3,
            ) *
              0.5 +
            0.25
          );
        });

  const bars = waveformSamples.map((sample, i) => {
    const angleRad =
      (i / barCount) * 2 * Math.PI + (rotationOffset * Math.PI) / 180;
    const dynamicHeight = Math.max(barMinHeight, sample * waveAmplitude);

    let startRadius: number;
    let endRadius: number;

    if (growOutwardsOnly) {
      startRadius = radius;
      endRadius = radius + dynamicHeight;
    } else {
      startRadius = radius - dynamicHeight / 2;
      endRadius = radius + dynamicHeight / 2;
    }

    const finalX1 = centerX + startRadius * Math.cos(angleRad);
    const finalY1 = centerY + startRadius * Math.sin(angleRad);
    const finalX2 = centerX + endRadius * Math.cos(angleRad);
    const finalY2 = centerY + endRadius * Math.sin(angleRad);

    return { x1: finalX1, y1: finalY1, x2: finalX2, y2: finalY2 };
  });

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <svg width="100%" height="100%" style={{ overflow: "visible" }}>
        {bars.map((bar, i) => (
          <line
            key={i}
            x1={bar.x1}
            y1={bar.y1}
            x2={bar.x2}
            y2={bar.y2}
            stroke={barColor}
            strokeWidth={barWidth}
            strokeLinecap="round"
          />
        ))}
      </svg>
    </AbsoluteFill>
  );
};
