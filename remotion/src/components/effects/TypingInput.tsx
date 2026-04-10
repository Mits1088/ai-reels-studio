import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

/**
 * TypingInput — Product-accurate typing input field animation.
 * Replicates the look of real product input fields (Google pill, Claude chat, generic).
 * Text appears character by character with a blinking cursor.
 */

type InputStyle = "google" | "claude" | "generic";

const STYLE_TOKENS: Record<
  InputStyle,
  {
    borderColor: string;
    focusBorderColor: string;
    backgroundColor: string;
    borderRadius: number;
    fontFamily: string;
    shadow: string;
    placeholderColor: string;
  }
> = {
  google: {
    borderColor: "#C6DAFC",
    focusBorderColor: "#4285F4",
    backgroundColor: "#FFFFFF",
    borderRadius: 999,
    fontFamily: "system-ui, 'Segoe UI', Roboto, sans-serif",
    shadow: "0 4px 20px rgba(66, 133, 244, 0.10)",
    placeholderColor: "rgba(0, 0, 0, 0.38)",
  },
  claude: {
    borderColor: "rgba(217, 119, 87, 0.3)",
    focusBorderColor: "#D97757",
    backgroundColor: "#FAF9F5",
    borderRadius: 24,
    fontFamily: "Inter, system-ui, sans-serif",
    shadow: "0 4px 20px rgba(217, 119, 87, 0.08)",
    placeholderColor: "rgba(0, 0, 0, 0.35)",
  },
  generic: {
    borderColor: "rgba(0, 0, 0, 0.15)",
    focusBorderColor: "rgba(0, 0, 0, 0.3)",
    backgroundColor: "#FFFFFF",
    borderRadius: 999,
    fontFamily: "system-ui, -apple-system, sans-serif",
    shadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
    placeholderColor: "rgba(0, 0, 0, 0.35)",
  },
};

export const TypingInput: React.FC<{
  text: string;
  suffix?: string;
  durationInFrames: number;
  typingSpeed?: number;
  cursorColor?: string;
  textColor?: string;
  accentColor?: string;
  fontSize?: number;
  borderColor?: string;
  backgroundColor?: string;
  borderRadius?: number;
  style?: InputStyle;
  placeholder?: string;
}> = ({
  text,
  suffix,
  durationInFrames,
  typingSpeed = 3,
  cursorColor: cursorColorProp,
  textColor: textColorProp,
  accentColor,
  fontSize: fontSizeProp,
  borderColor: borderColorProp,
  backgroundColor: backgroundColorProp,
  borderRadius: borderRadiusProp,
  style = "generic",
  placeholder,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const tokens = STYLE_TOKENS[style];

  // Resolve props with style defaults
  const cursorColor = cursorColorProp ?? "#000";
  const textColor = textColorProp ?? "#000";
  const fontSize = fontSizeProp ?? 28;
  const bgColor = backgroundColorProp ?? tokens.backgroundColor;
  const bRadius = borderRadiusProp ?? tokens.borderRadius;

  // Typing progress
  const totalTypingFrames = text.length * typingSpeed;
  const startDelay = 8; // small delay before typing starts
  const typingFrame = Math.max(0, frame - startDelay);
  const charsVisible = Math.min(text.length, Math.floor(typingFrame / typingSpeed));
  const visibleText = text.slice(0, charsVisible);
  const isDone = charsVisible >= text.length;
  const hasStarted = frame >= startDelay;

  // Blinking cursor (blink every 15 frames)
  const cursorBlink = isDone
    ? Math.floor(frame / 15) % 2 === 0
    : true;

  // Enter animation — field fades + scales in
  const enterOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const enterScale = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 120, mass: 0.8 },
  });

  // Exit animation
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 5, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Focus border animation — border becomes focus color once typing starts
  const focusProgress = interpolate(frame, [startDelay, startDelay + 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const baseBorderColor = borderColorProp ?? tokens.borderColor;
  const focusBorderColor = tokens.focusBorderColor;

  // Interpolate border color via opacity trick: layer focus border on top
  const borderStyle = `2px solid ${baseBorderColor}`;

  // Show placeholder before typing starts
  const showPlaceholder = placeholder && !hasStarted;

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        opacity: enterOpacity * exitOpacity,
        transform: `scale(${enterScale})`,
        zIndex: 40,
      }}
    >
      <div
        style={{
          position: "relative",
          width: "85%",
          maxWidth: 500,
        }}
      >
        {/* Base input field */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            backgroundColor: bgColor,
            borderRadius: bRadius,
            border: borderStyle,
            padding: `${Math.round(fontSize * 0.6)}px ${Math.round(fontSize * 0.85)}px`,
            boxShadow: tokens.shadow,
            fontFamily: tokens.fontFamily,
            fontSize,
            fontWeight: 400,
            color: textColor,
            whiteSpace: "nowrap",
            overflow: "hidden",
            boxSizing: "border-box" as const,
          }}
        >
          {/* Focus border overlay */}
          <div
            style={{
              position: "absolute",
              inset: -2,
              borderRadius: bRadius + 2,
              border: `2px solid ${focusBorderColor}`,
              opacity: focusProgress,
              pointerEvents: "none",
            }}
          />

          {/* Placeholder text */}
          {showPlaceholder && (
            <span
              style={{
                color: tokens.placeholderColor,
                userSelect: "none",
              }}
            >
              {placeholder}
            </span>
          )}

          {/* Typed text */}
          {hasStarted && (
            <>
              <span style={{ color: textColor }}>{visibleText}</span>
              {suffix && (
                <span style={{ color: accentColor ?? textColor, opacity: 0.7 }}>
                  {suffix}
                </span>
              )}
            </>
          )}

          {/* Blinking cursor */}
          {hasStarted && (
            <span
              style={{
                display: "inline-block",
                width: 2,
                height: fontSize * 1.2,
                backgroundColor: cursorColor,
                marginLeft: 2,
                opacity: cursorBlink ? 1 : 0,
                flexShrink: 0,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
