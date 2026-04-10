import React from "react";
import { AbsoluteFill, useCurrentFrame, random } from "remotion";

const FloatingParticles: React.FC<{ count?: number; color?: string }> = ({
  count = 30,
  color = "rgba(0, 229, 255, 0.15)",
}) => {
  const frame = useCurrentFrame();
  const particles = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      x: random(`px-${i}`) * 1080,
      y: random(`py-${i}`) * 1920,
      size: 2 + random(`ps-${i}`) * 5,
      speed: 0.3 + random(`psp-${i}`) * 0.8,
      drift: (random(`pd-${i}`) - 0.5) * 0.5,
      delay: random(`pdl-${i}`) * 200,
      opacity: 0.2 + random(`po-${i}`) * 0.5,
    }));
  }, [count]);

  return (
    <AbsoluteFill style={{ overflow: "hidden", zIndex: 1 }}>
      {particles.map((p, i) => {
        const y = (p.y - (frame + p.delay) * p.speed) % 2100;
        const adjustedY = y < -100 ? y + 2200 : y;
        const x = p.x + Math.sin((frame + p.delay) * 0.02) * 30 * p.drift;
        const pulse = 0.6 + Math.sin((frame + p.delay) * 0.05) * 0.4;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: adjustedY,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              background: color,
              opacity: p.opacity * pulse,
              boxShadow: `0 0 ${p.size * 3}px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const AnimatedBackground: React.FC = () => {
  const frame = useCurrentFrame();
  const angle = 180 + Math.sin(frame * 0.008) * 15;
  const hueShift = Math.sin(frame * 0.004) * 8;

  return (
    <AbsoluteFill>
      <div
        style={{
          width: "100%",
          height: "100%",
          background: `linear-gradient(${angle}deg,
            hsl(${215 + hueShift}, 30%, 6%) 0%,
            hsl(${220 + hueShift}, 25%, 9%) 40%,
            hsl(${225 + hueShift}, 30%, 6%) 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0, left: 0, right: 0, bottom: 0,
          background: `radial-gradient(ellipse at ${50 + Math.sin(frame * 0.006) * 15}% ${30 + Math.cos(frame * 0.005) * 10}%, rgba(0, 229, 255, 0.04) 0%, transparent 60%)`,
        }}
      />
      <FloatingParticles />
    </AbsoluteFill>
  );
};
