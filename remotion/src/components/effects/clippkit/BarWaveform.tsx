/**
 * BarWaveform — vendored from clippkit (MIT)
 * Source: https://github.com/reactvideoeditor/clippkit
 *         apps/docs/registry/default/components/bar-waveform.tsx
 *
 * Adapted for the AI Reels Studio pipeline:
 *  - Named export instead of default
 *  - Theme defaults (#D97757 coral)
 *  - Self-positioning AbsoluteFill for use as an OVERLAY_REGISTRY entry
 *  - Optional `position` prop (top / center / bottom) so it can sit at the
 *    bottom-of-frame as a "speech is happening" indicator during talking-head
 *    moments without covering the avatar's face
 *
 * Use it during avatar full-screen beats to add bottom-of-frame motion that
 * visualizes the actual narration audio. Pair with `audioData` from
 * `useAudioData(staticFile("source.wav"))` in the parent composition. When
 * `audioData` is omitted it falls back to a synthetic sine wave.
 */
import React from "react";
import {
  MediaUtilsAudioData,
  visualizeAudioWaveform,
} from "@remotion/media-utils";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

interface BarWaveformProps {
  audioData?: MediaUtilsAudioData | null;
  numberOfSamples?: number;
  barColor?: string;
  barWidth?: number;
  barGap?: number;
  waveAmplitude?: number;
  waveSpeed?: number;
  /** Vertical position of the waveform within the frame. */
  position?: "top" | "center" | "bottom";
  /** Inset from top or bottom edge in pixels. */
  paddingY?: number;
  /** Height of the waveform region in pixels. */
  height?: number;
  /** Width of the waveform region in pixels (defaults to full frame width). */
  width?: number;
  barBorderRadius?: number;
  growUpwardsOnly?: boolean;
  durationInFrames?: number;
}

export const BarWaveform: React.FC<BarWaveformProps> = ({
  audioData,
  numberOfSamples = 64,
  barColor = "#D97757",
  barWidth = 8,
  barGap = 6,
  waveAmplitude = 140,
  waveSpeed = 10,
  position = "bottom",
  paddingY = 80,
  height = 220,
  width,
  barBorderRadius = 4,
  growUpwardsOnly = false,
}) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, fps } = useVideoConfig();
  const finalWidth = width ?? videoWidth;

  const samples =
    audioData != null
      ? visualizeAudioWaveform({
          fps,
          frame,
          audioData,
          numberOfSamples,
          windowInSeconds: 1 / fps,
        })
      : Array(numberOfSamples)
          .fill(0)
          .map((_, i) => {
            return (
              Math.sin(
                frame / waveSpeed + (i / numberOfSamples) * 2 * Math.PI,
              ) *
                0.5 +
              0.5
            );
          });

  const barHeights = samples.map((s) => Math.max(1, s * waveAmplitude));
  const totalBarWidth = numberOfSamples * barWidth;
  const totalGapWidth = (numberOfSamples - 1) * barGap;
  const waveformVisualWidth = totalBarWidth + totalGapWidth;
  const startX = (finalWidth - waveformVisualWidth) / 2;

  const justifyContent =
    position === "top"
      ? "flex-start"
      : position === "bottom"
        ? "flex-end"
        : "center";

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent,
        paddingTop: position === "top" ? paddingY : 0,
        paddingBottom: position === "bottom" ? paddingY : 0,
        pointerEvents: "none",
      }}
    >
      <svg
        viewBox={`0 0 ${finalWidth} ${height}`}
        width={finalWidth}
        height={height}
      >
        {barHeights.map((barH, i) => {
          const x = startX + i * (barWidth + barGap);
          let rectY: number;
          let rectHeightValue: number;

          if (growUpwardsOnly) {
            const upwardHeight = barH / 2;
            rectY = height / 2 - upwardHeight;
            rectHeightValue =
              upwardHeight > 0
                ? Math.max(1, Math.min(upwardHeight, height / 2))
                : 0;
          } else {
            rectY = height / 2 - barH / 2;
            rectHeightValue =
              barH > 0 ? Math.max(1, Math.min(barH, height)) : 0;
          }

          return (
            <rect
              key={i}
              x={x}
              y={rectY}
              width={barWidth}
              height={rectHeightValue}
              fill={barColor}
              rx={barBorderRadius}
              ry={barBorderRadius}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
