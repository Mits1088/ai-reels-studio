import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

export interface ChartBarItem {
  label: string;
  value: number;
  color?: string;
}

/**
 * ChartBar — Data-driven animated bar chart.
 *
 * Bars grow upward from 0 via spring, staggered per bar.
 * Use for benchmark comparisons, stat breakdowns, capability charts.
 *
 * Example timeline.json overlay:
 * {
 *   "type": "ChartBar",
 *   "start": 4.0,
 *   "end": 8.0,
 *   "props": {
 *     "title": "Speed Comparison",
 *     "unit": "req/s",
 *     "data": [
 *       { "label": "GPT-4o", "value": 42, "color": "#10A37F" },
 *       { "label": "Claude 3", "value": 78, "color": "#D97757" },
 *       { "label": "Gemini", "value": 61, "color": "#4285F4" }
 *     ]
 *   }
 * }
 */
export const ChartBar: React.FC<{
  data: ChartBarItem[];
  title?: string;
  unit?: string;
  /** Override the max value (default: max of data values) */
  maxValue?: number;
  /** Default bar color when item has no color */
  barColor?: string;
  /** Frames between each bar's spring start (default 5) */
  staggerFrames?: number;
  durationInFrames: number;
}> = ({
  data,
  title,
  unit = "",
  maxValue,
  barColor = "#D97757",
  staggerFrames = 5,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Colors ────────────────────────────────────────────────────────────────
  const COLOR_LABEL = "rgba(255,255,255,0.85)";
  const COLOR_VALUE = "#FFFFFF";
  const COLOR_GRID = "rgba(255,255,255,0.10)";
  const BG_COLOR = "rgba(0,0,0,0.72)";

  // ── Layout ────────────────────────────────────────────────────────────────
  const CHART_HEIGHT = 320;
  const BAR_MAX_WIDTH = Math.max(60, Math.floor(680 / Math.max(data.length, 1)));
  const BAR_WIDTH = Math.min(BAR_MAX_WIDTH, 130);
  const FONT_FAMILY = "'Inter', system-ui, sans-serif";

  // ── Timing ────────────────────────────────────────────────────────────────
  const ENTER_FRAMES = 6;
  const EXIT_START = Math.max(0, durationInFrames - 5);

  const resolvedMax = maxValue ?? Math.max(...data.map((d) => d.value), 1);

  // ── Entry / exit opacity ──────────────────────────────────────────────────
  const entryOpacity = interpolate(frame, [0, ENTER_FRAMES], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(
    frame,
    [EXIT_START, Math.max(EXIT_START + 1, durationInFrames)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const combinedOpacity = entryOpacity * exitOpacity;

  // ── Title entry ───────────────────────────────────────────────────────────
  const titleOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: combinedOpacity,
      }}
    >
      <div
        style={{
          background: BG_COLOR,
          borderRadius: 24,
          padding: "36px 40px 32px",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.12)",
          boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
          minWidth: 520,
          maxWidth: 820,
        }}
      >
        {/* ── Title ────────────────────────────────────────────────────────── */}
        {title && (
          <div
            style={{
              fontSize: 36,
              fontWeight: 700,
              color: COLOR_VALUE,
              fontFamily: FONT_FAMILY,
              textAlign: "center",
              marginBottom: 32,
              letterSpacing: -0.5,
              opacity: titleOpacity,
            }}
          >
            {title}
          </div>
        )}

        {/* ── Chart area ───────────────────────────────────────────────────── */}
        <div
          style={{
            height: CHART_HEIGHT,
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "center",
            gap: 20,
            position: "relative",
          }}
        >
          {/* ── Grid lines (5 horizontal) ────────────────────────────────── */}
          {[0.25, 0.5, 0.75, 1.0].map((pct) => (
            <div
              key={pct}
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                bottom: CHART_HEIGHT * pct,
                height: 1,
                background: COLOR_GRID,
              }}
            />
          ))}

          {/* ── Bars ─────────────────────────────────────────────────────── */}
          {data.map((item, i) => {
            const springVal = spring({
              frame: frame - i * staggerFrames,
              fps,
              config: { damping: 14, stiffness: 180, mass: 0.8 },
            });
            const targetHeight = (item.value / resolvedMax) * CHART_HEIGHT;
            const barHeight = interpolate(springVal, [0, 1], [0, targetHeight], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const itemColor = item.color ?? barColor;
            const valueOpacity = interpolate(
              frame - i * staggerFrames,
              [10, 18],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 8,
                  position: "relative",
                }}
              >
                {/* Value label above bar */}
                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 800,
                    color: itemColor,
                    fontFamily: FONT_FAMILY,
                    opacity: valueOpacity,
                    position: "absolute",
                    bottom: barHeight + 8,
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.value.toLocaleString()}{unit}
                </div>

                {/* Bar */}
                <div
                  style={{
                    width: BAR_WIDTH,
                    height: barHeight,
                    background: `linear-gradient(to top, ${itemColor}, ${itemColor}CC)`,
                    borderRadius: "8px 8px 4px 4px",
                    boxShadow: `0 4px 20px ${itemColor}40`,
                    flexShrink: 0,
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* ── X-axis labels ─────────────────────────────────────────────────── */}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 20,
            marginTop: 14,
          }}
        >
          {data.map((item, i) => {
            const labelOpacity = interpolate(
              frame - i * staggerFrames,
              [8, 16],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            return (
              <div
                key={i}
                style={{
                  width: BAR_WIDTH,
                  textAlign: "center",
                  fontSize: 24,
                  fontWeight: 600,
                  color: COLOR_LABEL,
                  fontFamily: FONT_FAMILY,
                  opacity: labelOpacity,
                  lineHeight: 1.3,
                }}
              >
                {item.label}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
