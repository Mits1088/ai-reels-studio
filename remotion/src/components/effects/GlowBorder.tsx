import React from "react";
import { useCurrentFrame } from "remotion";

export const GlowBorder: React.FC<{
  children: React.ReactNode;
  color?: string;
  borderRadius?: number;
  intensity?: number;
}> = ({ children, color = "#00E5FF", borderRadius = 20, intensity = 1 }) => {
  const frame = useCurrentFrame();
  const angle = (frame * 3) % 360;
  const pulse = 0.7 + Math.sin(frame * 0.08) * 0.3;

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div
        style={{
          position: "absolute",
          inset: -2,
          borderRadius: borderRadius + 2,
          background: `conic-gradient(from ${angle}deg, ${color}, transparent 40%, ${color}80, transparent 70%, ${color})`,
          opacity: 0.6 * pulse * intensity,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius,
          border: `1.5px solid`,
          borderImage: `conic-gradient(from ${angle}deg, ${color}80, transparent 30%, ${color}60, transparent 60%, ${color}80) 1`,
          opacity: 0.5 * intensity,
        }}
      />
      <div style={{ position: "relative", width: "100%", height: "100%", borderRadius, overflow: "hidden" }}>
        {children}
      </div>
    </div>
  );
};
