import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

export const GlitchOverlay: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  if (frame >= durationInFrames) return null;

  const scanY = (frame * 137) % 1920;
  const glitchOpacity = interpolate(frame, [0, 2, durationInFrames], [0.6, 0.3, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ zIndex: 48, pointerEvents: "none", opacity: glitchOpacity }}>
      <div style={{
        position: "absolute",
        top: scanY, left: 0, right: 0,
        height: 3,
        background: "rgba(0, 229, 255, 0.4)",
        boxShadow: "0 0 8px rgba(0, 229, 255, 0.3)",
      }} />
      <div style={{
        position: "absolute",
        top: scanY + 20, left: 0, right: 0,
        height: 8 + random(`gs-${frame}`) * 15,
        background: "rgba(255, 0, 100, 0.08)",
        transform: `translateX(${(random(`gx-${frame}`) - 0.5) * 30}px)`,
      }} />
    </AbsoluteFill>
  );
};
