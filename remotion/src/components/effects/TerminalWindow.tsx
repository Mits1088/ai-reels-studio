import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

// ── Types ──────────────────────────────────────────────────────────────────

export interface TerminalLine {
  /** Text content of this line */
  text: string;
  /**
   * "command"  — typed char-by-char with prompt prefix + block cursor
   * "output"   — appears instantly (slightly dimmer)
   * "success"  — green (✓ Done, created, deployed, etc.)
   * "error"    — red  (✗ error, failed, etc.)
   * "info"     — gray (→ status, progress, etc.)
   */
  type?: "command" | "output" | "success" | "error" | "info";
  /** Absolute frame within the Sequence when this line starts appearing */
  startFrame?: number;
  /** Characters revealed per frame for command lines (default 1.5 ≈ 45 cps at 30fps) */
  charsPerFrame?: number;
  /** Skip typing animation and appear immediately (useful for pre-filled output blocks) */
  instant?: boolean;
}

export interface TerminalWindowProps {
  lines: TerminalLine[];
  /** Shell prompt prefix (default "$ ") */
  prompt?: string;
  /** macOS title bar label */
  title?: string;
  /**
   * 3D perspective oscillation — subtle tilt on X and Y axes.
   * Good for "showcase" moments (hook demo, CTA).
   */
  tilt?: boolean;
  fontSize?: number;
  durationInFrames: number;
  style?: React.CSSProperties;
}

// ── Color palette (GitHub Dark) ────────────────────────────────────────────

const BG      = "#0D1117";
const TITLE_BAR_BG = "#161B22";
const BORDER  = "rgba(48,54,61,1)";
const PROMPT_COLOR = "#79C0FF";  // blue

const LINE_COLORS: Record<string, string> = {
  command: "#E6EDF3",
  output:  "#C9D1D9",
  success: "#3FB950",
  error:   "#F85149",
  info:    "#8B949E",
};

const TRAFFIC_LIGHTS = ["#FF5F56", "#FFBD2E", "#27C93F"] as const;

// ── Helpers ────────────────────────────────────────────────────────────────

function charsForLine(line: TerminalLine, frame: number): number {
  const start = line.startFrame ?? 0;
  if (frame < start) return 0;
  if (line.type !== "command" || line.instant) return line.text.length;
  const elapsed = frame - start;
  return Math.min(line.text.length, Math.floor(elapsed * (line.charsPerFrame ?? 1.5)));
}

// ── Component ──────────────────────────────────────────────────────────────

/**
 * TerminalWindow — multi-line terminal with macOS chrome and typing animation.
 *
 * Renders as a floating card centered in an AbsoluteFill — use in the overlays
 * lane (type: "TerminalWindow") to overlay on top of demo content or avatar.
 *
 * Example timeline.json entry:
 * {
 *   "type": "TerminalWindow",
 *   "start": 5.0,
 *   "end": 12.0,
 *   "props": {
 *     "title": "Terminal",
 *     "tilt": true,
 *     "fontSize": 26,
 *     "lines": [
 *       { "text": "claude --model claude-opus-4-7 -p 'Write deploy.sh'", "type": "command", "startFrame": 0 },
 *       { "text": "→ Generating deploy.sh ...", "type": "info", "startFrame": 48 },
 *       { "text": "✓  deploy.sh created (42 lines)", "type": "success", "startFrame": 60 }
 *     ]
 *   }
 * }
 */
export const TerminalWindow: React.FC<TerminalWindowProps> = ({
  lines,
  prompt = "$ ",
  title = "Terminal",
  tilt = false,
  fontSize = 28,
  durationInFrames,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entry: fast spring scale-pop + opacity ───────────────────────────────
  const entrySpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 220, mass: 0.8 },
  });
  const entryScale = interpolate(entrySpring, [0, 1], [0.88, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const entryOpacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Exit: quick fade out ─────────────────────────────────────────────────
  const safeExitStart = Math.max(0, durationInFrames - 4);
  const exitOpacity = interpolate(
    frame,
    [safeExitStart, Math.max(safeExitStart + 1, durationInFrames)],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // ── 3D perspective tilt (deterministic — Math.sin/cos are fine) ──────────
  // Uses sin/cos of frame count: completely deterministic, no Math.random()
  const tiltX = tilt ? Math.sin(frame * 0.025) * 4 : 0;  // ±4° on X
  const tiltY = tilt ? Math.cos(frame * 0.015) * 2 : 0;  // ±2° on Y

  // ── Deterministic cursor blink (15 frames ≈ 0.5s period at 30fps) ────────
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Find the last command line that has started — cursor lives here
  let cursorLineIdx = -1;
  for (let i = lines.length - 1; i >= 0; i--) {
    const l = lines[i];
    if (l.type === "command" && frame >= (l.startFrame ?? 0)) {
      cursorLineIdx = i;
      break;
    }
  }

  const TITLE_H = 38;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "56px 44px",
        perspective: tilt ? "1200px" : undefined,
        opacity: entryOpacity * exitOpacity,
      }}
    >
      {/* ── Terminal card ─────────────────────────────────────────────── */}
      <div
        style={{
          width: "100%",
          maxHeight: "100%",
          borderRadius: 12,
          overflow: "hidden",
          border: `1px solid ${BORDER}`,
          boxShadow: "0 36px 100px rgba(0,0,0,0.82), 0 8px 28px rgba(0,0,0,0.55)",
          display: "flex",
          flexDirection: "column",
          transform: `scale(${entryScale}) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`,
          transformStyle: "preserve-3d",
          ...style,
        }}
      >
        {/* ── Title bar ──────────────────────────────────────────────── */}
        <div
          style={{
            height: TITLE_H,
            flexShrink: 0,
            background: TITLE_BAR_BG,
            borderBottom: `1px solid ${BORDER}`,
            display: "flex",
            alignItems: "center",
            paddingLeft: 14,
            paddingRight: 14,
            position: "relative",
          }}
        >
          {/* Traffic lights */}
          <div style={{ display: "flex", gap: 7, alignItems: "center" }}>
            {TRAFFIC_LIGHTS.map((color, idx) => (
              <div
                key={idx}
                style={{ width: 12, height: 12, borderRadius: "50%", background: color }}
              />
            ))}
          </div>

          {/* Centered title */}
          <span
            style={{
              position: "absolute",
              left: "50%",
              transform: "translateX(-50%)",
              fontSize: 13,
              fontWeight: 500,
              color: "rgba(230,237,243,0.58)",
              fontFamily: "system-ui, -apple-system, sans-serif",
              lineHeight: 1,
              whiteSpace: "nowrap",
              letterSpacing: -0.2,
              pointerEvents: "none",
            }}
          >
            {title}
          </span>
        </div>

        {/* ── Terminal content ────────────────────────────────────────── */}
        <div
          style={{
            background: BG,
            padding: "18px 22px 22px",
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
            fontSize,
            lineHeight: 1.75,
          }}
        >
          {lines.map((line, i) => {
            const start = line.startFrame ?? 0;
            if (frame < start) return null;

            const charsShown = charsForLine(line, frame);
            const visibleText = line.text.slice(0, charsShown);
            const isCurrentCursorLine = i === cursorLineIdx;
            const isTyping = line.type === "command" && !line.instant && charsShown < line.text.length;
            const lineColor = LINE_COLORS[line.type ?? "output"] ?? LINE_COLORS.output;

            // Per-line opacity: non-command lines get a quick 4-frame fade-in
            const lineOpacity =
              line.type === "command"
                ? 1
                : interpolate(frame - start, [0, 4], [0, 1], {
                    extrapolateLeft: "clamp",
                    extrapolateRight: "clamp",
                  });

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  opacity: lineOpacity,
                  minHeight: `${fontSize * 1.75}px`,
                }}
              >
                {/* Prompt prefix — only for command lines */}
                {line.type === "command" && (
                  <span
                    style={{
                      color: PROMPT_COLOR,
                      flexShrink: 0,
                      userSelect: "none",
                      opacity: interpolate(frame - start, [0, 3], [0, 1], {
                        extrapolateLeft: "clamp",
                        extrapolateRight: "clamp",
                      }),
                    }}
                  >
                    {prompt}
                  </span>
                )}

                {/* Line text */}
                <span style={{ color: lineColor, wordBreak: "break-all" }}>
                  {visibleText}

                  {/* Block cursor — shown on the active command line */}
                  {isCurrentCursorLine && (isTyping || cursorVisible) && (
                    <span
                      style={{
                        display: "inline-block",
                        width: "0.6em",
                        height: "1em",
                        background: LINE_COLORS.command,
                        marginLeft: 2,
                        verticalAlign: "text-bottom",
                        opacity: isTyping ? 1 : (cursorVisible ? 1 : 0),
                      }}
                    />
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
