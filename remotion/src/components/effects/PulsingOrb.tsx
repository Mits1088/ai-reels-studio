import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

/**
 * PulsingOrb — Glowing energy orb with pulsing rings.
 * Use for emphasis, energy visualization, or abstract tech feel.
 */
export const PulsingOrb: React.FC<{
  x?: number;
  y?: number;
  size?: number;
  color?: string;
  durationInFrames: number;
}> = ({
  x = 50,
  y = 50,
  size = 80,
  color = "#00E5FF",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const enter = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const visibility = enter * exit;

  // Core pulse
  const pulse = 1 + Math.sin(frame * 0.1) * 0.08;

  // Outer rings expand
  const ring1 = 1 + ((frame * 0.02) % 1) * 0.8;
  const ring1Opacity = 1 - ((frame * 0.02) % 1);
  const ring2 = 1 + (((frame * 0.02) + 0.5) % 1) * 0.8;
  const ring2Opacity = 1 - (((frame * 0.02) + 0.5) % 1);

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: "translate(-50%, -50%)",
        opacity: visibility,
        zIndex: 35,
        pointerEvents: "none",
      }}
    >
      {/* Expanding rings */}
      {[{ scale: ring1, opacity: ring1Opacity }, { scale: ring2, opacity: ring2Opacity }].map((ring, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: "50%", top: "50%",
            width: size, height: size,
            marginLeft: -size / 2, marginTop: -size / 2,
            borderRadius: "50%",
            border: `1px solid ${color}`,
            transform: `scale(${ring.scale})`,
            opacity: ring.opacity * 0.4,
          }}
        />
      ))}
      {/* Core orb */}
      <div
        style={{
          width: size * 0.4,
          height: size * 0.4,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${color}90, ${color}40 50%, transparent 70%)`,
          transform: `scale(${pulse})`,
          boxShadow: `0 0 ${size * 0.3}px ${color}30, 0 0 ${size * 0.6}px ${color}15`,
          position: "relative",
          left: size * 0.3, top: size * 0.3,
        }}
      />
    </div>
  );
};
