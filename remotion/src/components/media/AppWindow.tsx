import React from "react";

const TRAFFIC_LIGHTS = ["#FF5F56", "#FFBD2E", "#27C93F"] as const;

export interface AppWindowProps {
  platform?: "macos" | "chrome";
  theme?: "light" | "dark";
  url?: string;
  title?: string;
  showUrlBar?: boolean;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}

/**
 * AppWindow — browser/app window chrome wrapper.
 *
 * Wraps screenshots or videos inside a macOS-style title bar with traffic lights
 * and an optional URL bar. Pure presentational — no frame-based animation.
 *
 * Usage in timeline.json:
 *   demo lane entry with display: "app-window"
 *   entry.appWindow = { platform: "macos", theme: "light", url: "claude.ai", showUrlBar: true }
 *
 * Or use directly in JSX:
 *   <AppWindow url="claude.ai" showUrlBar><FramedImage src="..." /></AppWindow>
 */
export const AppWindow: React.FC<AppWindowProps> = ({
  theme = "light",
  url,
  title,
  showUrlBar = false,
  children,
  style,
}) => {
  const isDark = theme === "dark";

  const TITLE_H = 40;
  const URL_H = showUrlBar && url ? 36 : 0;

  const borderColor = isDark ? "rgba(48,54,61,0.9)" : "rgba(0,0,0,0.12)";

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        borderRadius: 10,
        overflow: "hidden",
        border: `1px solid ${borderColor}`,
        boxShadow: isDark
          ? "0 24px 72px rgba(0,0,0,0.72), 0 4px 20px rgba(0,0,0,0.5)"
          : "0 24px 72px rgba(0,0,0,0.28), 0 4px 16px rgba(0,0,0,0.18)",
        display: "flex",
        flexDirection: "column",
        ...style,
      }}
    >
      {/* ── Title bar ─────────────────────────────────────────────── */}
      <div
        style={{
          height: TITLE_H,
          flexShrink: 0,
          background: isDark ? "#2D2D2D" : "#E8E8E8",
          display: "flex",
          alignItems: "center",
          paddingLeft: 14,
          paddingRight: 14,
          position: "relative",
          borderBottom: `1px solid ${borderColor}`,
        }}
      >
        {/* Traffic lights */}
        <div style={{ display: "flex", gap: 7, alignItems: "center", zIndex: 1 }}>
          {TRAFFIC_LIGHTS.map((color, idx) => (
            <div
              key={idx}
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                background: color,
                flexShrink: 0,
              }}
            />
          ))}
        </div>

        {/* Centered title */}
        {title && (
          <span
            style={{
              position: "absolute",
              left: "50%",
              transform: "translateX(-50%)",
              fontSize: 13,
              fontWeight: 500,
              color: isDark ? "rgba(255,255,255,0.68)" : "rgba(0,0,0,0.55)",
              fontFamily: "system-ui, -apple-system, sans-serif",
              lineHeight: 1,
              whiteSpace: "nowrap",
              letterSpacing: -0.2,
              pointerEvents: "none",
            }}
          >
            {title}
          </span>
        )}
      </div>

      {/* ── URL bar (optional) ────────────────────────────────────── */}
      {showUrlBar && url && (
        <div
          style={{
            height: URL_H,
            flexShrink: 0,
            background: isDark ? "#383838" : "#F0F0F0",
            display: "flex",
            alignItems: "center",
            paddingLeft: 12,
            paddingRight: 12,
            borderBottom: `1px solid ${borderColor}`,
          }}
        >
          {/* Lock icon placeholder */}
          <span
            style={{
              fontSize: 11,
              color: isDark ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.35)",
              marginRight: 6,
              flexShrink: 0,
            }}
          >
            🔒
          </span>

          {/* URL pill */}
          <div
            style={{
              flex: 1,
              height: 22,
              background: isDark ? "rgba(255,255,255,0.09)" : "rgba(0,0,0,0.07)",
              borderRadius: 4,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              overflow: "hidden",
            }}
          >
            <span
              style={{
                fontSize: 12,
                color: isDark ? "rgba(255,255,255,0.52)" : "rgba(0,0,0,0.45)",
                fontFamily: "system-ui, -apple-system, sans-serif",
                lineHeight: 1,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: "90%",
              }}
            >
              {url}
            </span>
          </div>
        </div>
      )}

      {/* ── Content ───────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflow: "hidden", minHeight: 0, background: isDark ? "#1e1e1e" : "#ffffff" }}>
        {children}
      </div>
    </div>
  );
};
